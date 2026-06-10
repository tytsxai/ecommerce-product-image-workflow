import React from "react";
import { createRoot } from "react-dom/client";
import {
  Check,
  Download,
  ImagePlus,
  Layers3,
  PackagePlus,
  Play,
  RefreshCw,
  Settings2,
  Upload,
  X
} from "lucide-react";
import "./styles.css";

type BatchPayload = {
  batch: { id: number; name: string; project_name: string; status: string };
  products: Product[];
  jobs: Job[];
  assets: Asset[];
};

type Product = {
  id: number;
  product_id: string;
  product_name_en: string;
  style_pack: string;
  source_images: SourceImage[];
};

type SourceImage = { id: number; filename: string; media_url: string };
type Job = { id: number; category: string; slot: number; status: string; error?: string };
type Asset = {
  id: number;
  category: string;
  filename: string;
  media_url: string;
  reviews: { decision: string; reject_tag?: string; notes?: string }[];
};

type Provider = {
  provider_id: string;
  display_name: string;
  capabilities: Record<string, unknown>;
  required_env: string[];
  request_schema: Record<string, unknown>;
};

const defaultProduct = {
  product_id: "SKU123",
  product_name_en: "Stainless Steel Insulated Tumbler",
  style_pack: "minimal_white",
  specs: ["Capacity: 500 ml", "Double-wall insulation", "Leak-proof lid"],
  steps: ["Fill with your drink", "Close the lid firmly", "Enjoy hot or cold beverages"],
  tips: ["Hand wash recommended"]
};

function App() {
  const [batch, setBatch] = React.useState<BatchPayload | null>(null);
  const [providers, setProviders] = React.useState<Provider[]>([]);
  const [stylePacks, setStylePacks] = React.useState<{ pack_id: string; scene: string }[]>([]);
  const [providerId, setProviderId] = React.useState("local_mock");
  const [model, setModel] = React.useState("local-placeholder");
  const [providerConfig, setProviderConfig] = React.useState("{}");
  const [productForm, setProductForm] = React.useState(defaultProduct);
  const [selectedProductId, setSelectedProductId] = React.useState<number | null>(null);
  const [message, setMessage] = React.useState("");
  const [busyAction, setBusyAction] = React.useState<string | null>(null);

  React.useEffect(() => {
    void bootstrap().catch((error: unknown) => setMessage(errorMessage(error)));
  }, []);

  React.useEffect(() => {
    if (!batch?.batch.id) return;
    const timer = window.setInterval(() => {
      void refreshBatch(batch.batch.id).catch((error: unknown) => setMessage(errorMessage(error)));
    }, 1500);
    return () => window.clearInterval(timer);
  }, [batch?.batch.id]);

  async function runAction(actionName: string, action: () => Promise<void>) {
    if (busyAction) return;
    setBusyAction(actionName);
    try {
      await action();
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setBusyAction(null);
    }
  }

  async function bootstrap() {
    const [providerData, styleData, batchesData] = await Promise.all([
      api<{ providers: Provider[] }>("/api/providers"),
      api<{ style_packs: { pack_id: string; scene: string }[] }>("/api/style-packs"),
      api<{ batches: { id: number }[] }>("/api/batches")
    ]);
    setProviders(providerData.providers);
    setStylePacks(styleData.style_packs);
    if (batchesData.batches[0]) {
      await refreshBatch(batchesData.batches[0].id);
    } else {
      await createBatch();
    }
  }

  async function createBatch() {
    const data = await api<BatchPayload>("/api/batches", {
      method: "POST",
      body: JSON.stringify({ project_name: "Demo Store", batch_name: "New Product Image Batch" })
    });
    setBatch(data);
    setSelectedProductId(null);
    setMessage("Batch created.");
  }

  async function refreshBatch(batchId: number) {
    const data = await api<BatchPayload>(`/api/batches/${batchId}`);
    setBatch(data);
    if (!selectedProductId && data.products[0]) setSelectedProductId(data.products[0].id);
  }

  async function addProduct() {
    if (!batch) return;
    const data = await api<{ product: Product }>(`/api/batches/${batch.batch.id}/products`, {
      method: "POST",
      body: JSON.stringify(productForm)
    });
    setSelectedProductId(data.product.id);
    await refreshBatch(batch.batch.id);
    setMessage("Product added.");
  }

  async function uploadSource(file: File) {
    if (!selectedProductId || !batch) return;
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`/api/products/${selectedProductId}/source-images`, { method: "POST", body: form });
    if (!res.ok) throw new Error(await responseErrorText(res));
    await refreshBatch(batch.batch.id);
    setMessage("Source image uploaded.");
  }

  async function generate() {
    if (!batch) return;
    let config = {};
    try {
      config = JSON.parse(providerConfig || "{}");
    } catch {
      setMessage("Provider config must be valid JSON.");
      return;
    }
    const data = await api<{ jobs: Job[] }>(`/api/batches/${batch.batch.id}/generate`, {
      method: "POST",
      body: JSON.stringify({ provider_id: providerId, model, config })
    });
    await refreshBatch(batch.batch.id);
    setMessage(data.jobs.length ? "Generation queued." : "All generation slots already have successful assets.");
  }

  async function review(assetId: number, decision: "pass" | "reject") {
    if (!batch) return;
    await api(`/api/assets/${assetId}/review`, {
      method: "POST",
      body: JSON.stringify({
        decision,
        reject_tag: decision === "reject" ? "product_changed" : undefined,
        reviewer: "manager",
        notes: decision === "pass" ? "Approved in workbench" : "Needs rework"
      })
    });
    await refreshBatch(batch.batch.id);
    setMessage(decision === "pass" ? "Asset approved." : "Asset rejected.");
  }

  async function retry(assetId: number) {
    if (!batch) return;
    await api(`/api/assets/${assetId}/retry`, { method: "POST" });
    await refreshBatch(batch.batch.id);
    setMessage("Retry queued.");
  }

  const selectedProduct = batch?.products.find((p) => p.id === selectedProductId) || batch?.products[0];
  const sourceImage = selectedProduct?.source_images[0];
  const approved = batch?.assets.filter((a) => a.reviews[0]?.decision === "pass").length || 0;
  const activeJobs = batch?.jobs.some((job) => job.status === "queued" || job.status === "running") || false;
  const busy = busyAction !== null;
  const canGenerate = Boolean(batch?.products.length) && !activeJobs && !busy;

  return (
    <main className="shell">
      <aside className="rail">
        <div className="brand">
          <Layers3 size={22} />
          <div>
            <strong>Image Workflow</strong>
            <span>Local AI workbench</span>
          </div>
        </div>
        <button onClick={() => void runAction("createBatch", createBatch)} disabled={busy}><PackagePlus size={17} /> New batch</button>
        <button onClick={() => void runAction("generate", generate)} disabled={!canGenerate}><Play size={17} /> Generate</button>
        <a className="button" href={batch ? `/api/batches/${batch.batch.id}/export` : "#"}>
          <Download size={17} /> Export approved
        </a>
        <div className="status">
          <span>{batch?.products.length || 0} products</span>
          <span>{batch?.jobs.length || 0} jobs</span>
          <span>{approved} approved</span>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p>{batch?.batch.project_name || "Demo Store"}</p>
            <h1>{batch?.batch.name || "Product Image Batch"}</h1>
          </div>
          <span className="pill">{batch?.batch.status || "draft"}</span>
        </header>

        <section className="columns">
          <div className="panel intake">
            <div className="panelTitle"><ImagePlus size={18} /> Product intake</div>
            <label>SKU<input value={productForm.product_id} onChange={(e) => setProductForm({ ...productForm, product_id: e.target.value })} /></label>
            <label>English name<input value={productForm.product_name_en} onChange={(e) => setProductForm({ ...productForm, product_name_en: e.target.value })} /></label>
            <label>Style pack
              <select value={productForm.style_pack} onChange={(e) => setProductForm({ ...productForm, style_pack: e.target.value })}>
                {stylePacks.map((pack) => <option key={pack.pack_id} value={pack.pack_id}>{pack.pack_id} · {pack.scene}</option>)}
              </select>
            </label>
            <label>Specs<textarea value={productForm.specs.join("\n")} onChange={(e) => setProductForm({ ...productForm, specs: splitLines(e.target.value) })} /></label>
            <label>Steps<textarea value={productForm.steps.join("\n")} onChange={(e) => setProductForm({ ...productForm, steps: splitLines(e.target.value) })} /></label>
            <button onClick={() => void runAction("addProduct", addProduct)} disabled={busy}><PackagePlus size={17} /> Add product</button>
            <label className={`upload ${busy ? "disabled" : ""}`}><Upload size={18} /> Upload supplier image<input type="file" accept="image/*" disabled={busy} onChange={(e) => e.target.files?.[0] && void runAction("uploadSource", () => uploadSource(e.target.files![0]))} /></label>
          </div>

          <div className="panel production">
            <div className="panelTitle"><Settings2 size={18} /> Model and jobs</div>
            <div className="modelRow">
              <select value={providerId} onChange={(e) => setProviderId(e.target.value)}>
                {providers.map((p) => <option key={p.provider_id} value={p.provider_id}>{p.display_name}</option>)}
              </select>
              <input value={model} onChange={(e) => setModel(e.target.value)} />
            </div>
            <textarea className="config" value={providerConfig} onChange={(e) => setProviderConfig(e.target.value)} />
            <div className="productList">
              {batch?.products.map((product) => (
                <button className={product.id === selectedProduct?.id ? "selected" : ""} key={product.id} onClick={() => setSelectedProductId(product.id)}>
                  {product.product_id}<span>{product.product_name_en}</span>
                </button>
              ))}
            </div>
            <div className="jobGrid">
              {batch?.jobs.slice(0, 14).map((job) => <span key={job.id} className={`job ${job.status}`}>{job.category} {job.slot} · {job.status}</span>)}
            </div>
          </div>

          <div className="panel review">
            <div className="panelTitle"><Check size={18} /> QA review</div>
            <div className="compare">
              <div>{sourceImage ? <img src={sourceImage.media_url} /> : <div className="empty">Supplier image</div>}<span>Source</span></div>
              <div>{batch?.assets[0] ? <img src={batch.assets[0].media_url} /> : <div className="empty">Generated image</div>}<span>Output</span></div>
            </div>
            <div className="assets">
              {batch?.assets.map((asset) => (
                <article key={asset.id}>
                  <img src={asset.media_url} />
                  <div>
                    <strong>{asset.category}</strong>
                    <span>{asset.reviews[0]?.decision || "unreviewed"}</span>
                  </div>
                  <button title="Pass" disabled={busy} onClick={() => void runAction("reviewPass", () => review(asset.id, "pass"))}><Check size={16} /></button>
                  <button title="Reject" disabled={busy} onClick={() => void runAction("reviewReject", () => review(asset.id, "reject"))}><X size={16} /></button>
                  <button title="Retry" disabled={busy} onClick={() => void runAction("retry", () => retry(asset.id))}><RefreshCw size={16} /></button>
                </article>
              ))}
            </div>
          </div>
        </section>
        <footer>{busyAction ? "Working..." : message || "Ready. Create or open a batch, add products, choose a provider, then generate."}</footer>
      </section>
    </main>
  );
}

async function api<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { headers: { "Content-Type": "application/json", ...(init?.headers || {}) }, ...init });
  if (!res.ok) throw new Error(await responseErrorText(res));
  return res.json();
}

async function responseErrorText(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const parsed = JSON.parse(text) as { detail?: unknown };
    if (typeof parsed.detail === "string") return parsed.detail;
  } catch {
    // Fall back to the raw response body below.
  }
  return text || `${res.status} ${res.statusText}`;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Request failed.";
}

function splitLines(value: string): string[] {
  return value.split("\n").map((line) => line.trim()).filter(Boolean);
}

createRoot(document.getElementById("root")!).render(<App />);
