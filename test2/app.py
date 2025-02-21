from flask import Flask, request, jsonify
import random
from collections import defaultdict

# OpenTelemetry
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from prometheus_client import Counter, generate_latest

# Initialisation OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(exporter))

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
    app.run(debug=True)
