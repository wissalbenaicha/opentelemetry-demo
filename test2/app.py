from flask import Flask, request, jsonify
import random
from collections import defaultdict

# OpenTelemetry
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Prometheus
from prometheus_client import Counter, generate_latest

# Initialisation OpenTelemetry avec un service.name unique
trace_provider = TracerProvider(resource=Resource.create({
    "service.name": "test2-app"
}))
trace.set_tracer_provider(trace_provider)
exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(exporter))
tracer = trace.get_tracer("test2-app")

# Flask App
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# Stockage temporaire des recherches
search_counts = defaultdict(int)

# Prometheus Metrics
REQUEST_COUNT = Counter("http_requests_total", "Nombre total de requêtes", ["endpoint"])
SEARCH_COUNT = Counter("search_requests_total", "Nombre de recherches par produit", ["product"])

@app.route("/")
def home():
    REQUEST_COUNT.labels(endpoint="/").inc()
    return "Bienvenue sur notre site e-commerce !"

@app.route("/search")
def search():
    product = request.args.get("product", "unknown")
    search_counts[product] += 1
    SEARCH_COUNT.labels(product=product).inc()

    with tracer.start_as_current_span("search_product"):
        return jsonify({"message": f"Recherche effectuée pour {product}"})

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": "text/plain"}

@app.route("/top-searches")
def top_searches():
    top_products = sorted(search_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return jsonify({"top_searched_products": top_products})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
