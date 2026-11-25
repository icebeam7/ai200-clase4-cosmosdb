using System.Net.Http.Headers;
using System.Text;
using Azure.Core;
using Azure.Identity;
using Microsoft.Azure.Cosmos;
using Newtonsoft.Json.Linq;

// Procesador REAL del SDK .NET: leases, checkpoint y distribución de particiones.
// Observa documents y actualiza documents_vectors. El worker debe estar ejecutándose
// ANTES de ejecutar el paso de actualización del laboratorio 4.
string Required(string name) => Environment.GetEnvironmentVariable(name)
    ?? throw new InvalidOperationException($"Falta variable {name}");
var endpoint = Required("COSMOS_ENDPOINT");
var key = Required("COSMOS_KEY");
var database = Environment.GetEnvironmentVariable("COSMOS_DATABASE") ?? "ai200docs";
var sourceName = Environment.GetEnvironmentVariable("COSMOS_SOURCE_CONTAINER") ?? "documents";
var vectorName = Environment.GetEnvironmentVariable("COSMOS_VECTOR_CONTAINER") ?? "documents_vectors";
var leasesName = Environment.GetEnvironmentVariable("COSMOS_LEASE_CONTAINER") ?? "leases";
var model = Required("EMBEDDING_DEPLOYMENT");
var openAiEndpoint = Required("FOUNDRY_OPENAI_ENDPOINT").TrimEnd('/');
int dimensions = int.Parse(Environment.GetEnvironmentVariable("EMBEDDING_DIMENSIONS") ?? "1536");

using var cosmos = new CosmosClient(endpoint, key);
var source = cosmos.GetContainer(database, sourceName);
var vector = cosmos.GetContainer(database, vectorName);
var leases = cosmos.GetContainer(database, leasesName);
var identity = new DefaultAzureCredential();
using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(90) };

async Task<JArray> Embed(string content, CancellationToken ct)
{
    var token = await identity.GetTokenAsync(
        new TokenRequestContext(new[] { "https://ai.azure.com/.default" }), ct);
    using var request = new HttpRequestMessage(HttpMethod.Post, $"{openAiEndpoint}/embeddings");
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token.Token);
    request.Content = new StringContent(
        new JObject { ["model"] = model, ["input"] = content }.ToString(),
        Encoding.UTF8, "application/json");
    using var response = await http.SendAsync(request, ct);
    string body = await response.Content.ReadAsStringAsync(ct);
    if (!response.IsSuccessStatusCode)
        throw new InvalidOperationException($"Foundry HTTP {(int)response.StatusCode}: {body}");
    var embedding = (JArray?)JObject.Parse(body)["data"]?[0]?["embedding"]
        ?? throw new InvalidOperationException("Foundry no devolvió un embedding.");
    if (embedding.Count != dimensions)
        throw new InvalidOperationException($"Dimensiones {embedding.Count}, esperadas {dimensions}");
    return embedding;
}

async Task HandleChanges(IReadOnlyCollection<JObject> changes, CancellationToken ct)
{
    foreach (var doc in changes)
    {
        var id = doc.Value<string>("id") ?? throw new InvalidOperationException("Documento sin id");
        var tenant = doc.Value<string>("tenant") ?? throw new InvalidOperationException("Documento sin tenant");
        var text = $"{doc.Value<string>("title")}\n{doc.Value<string>("content")}";
        var clean = (JObject)doc.DeepClone();
        foreach (var keyToRemove in new[] { "_rid", "_self", "_etag", "_attachments", "_ts", "_lsn" })
            clean.Remove(keyToRemove);
        clean["embedding"] = await Embed(text, ct);
        await vector.UpsertItemAsync(clean, new PartitionKey(tenant), cancellationToken: ct);
        Console.WriteLine($"[Change Feed] {DateTimeOffset.UtcNow:O} indexado: {id}");
    }
}

var processor = source.GetChangeFeedProcessorBuilder<JObject>("ai200-embedding-indexer", HandleChanges)
    .WithInstanceName($"worker-{Environment.MachineName}")
    .WithLeaseContainer(leases)
    .Build();

using var stop = new CancellationTokenSource();
Console.CancelKeyPress += (_, e) => { e.Cancel = true; stop.Cancel(); };
await processor.StartAsync();
Console.WriteLine("Change Feed Processor iniciado. Modifica un documento en otra terminal; Ctrl+C para terminar.");
try { await Task.Delay(Timeout.Infinite, stop.Token); }
catch (OperationCanceledException) { }
finally { await processor.StopAsync(); }
