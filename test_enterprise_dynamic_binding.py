import os
import sys
import json
import urllib.request
import subprocess

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

print("=============================================================")
print("🚀 TENDERPULSE 4IR ENTERPRISE DYNAMIC BINDING TEST SUITE")
print("=============================================================")

# 1. HTTP Server & Asset Verification
server_url = "http://127.0.0.1:8080"
assets = [
    "/",
    "/index.html",
    "/js/services/spatialGis.js",
    "/js/state.js",
    "/js/sar-3d.js",
    "/js/cartel-3d.js",
    "/js/ecms-hub.js",
    "/js/calculator.js",
    "/js/app.js"
]

print("\n[STEP 1] Testing Server Delivery of Web Assets...")
for asset in assets:
    url = server_url + asset
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'TenderPulseTestRunner/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            content_len = len(response.read())
            assert status == 200, f"Expected status 200 for {asset}, got {status}"
            assert content_len > 100, f"File {asset} appears too short ({content_len} bytes)"
            print(f"  [PASS] {asset} -> HTTP {status} ({content_len} bytes)")
    except Exception as e:
        print(f"  [FAIL] Error loading {url}: {e}")
        sys.exit(1)

# 2. Node.js Dynamic Binding & Spatial GIS Integration Test
print("\n[STEP 2] Executing Node.js Simulation for Dynamic Data-Binding...")

node_test_script = """
const fs = require('fs');

// Mock window and document environment
global.window = global;
global.document = {
  querySelectorAll: () => [],
  getElementById: (id) => ({
    style: {},
    classList: { add: () => {}, remove: () => {} },
    getContext: () => ({
      clearRect: () => {},
      beginPath: () => {},
      arc: () => {},
      fill: () => {},
      stroke: () => {},
      fillText: () => {},
      measureText: () => ({ width: 50 }),
      save: () => {},
      restore: () => {},
      roundRect: () => {},
      createLinearGradient: () => ({ addColorStop: () => {} })
    }),
    addEventListener: () => {},
    innerHTML: '',
    textContent: ''
  })
};
global.localStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {}
};
global.alert = (msg) => console.log('  [Alert Modal]:', msg);

// Load Spatial GIS
require('./js/services/spatialGis.js');
const spatialGIS = window.spatialGIS;

if (!spatialGIS) {
  console.error('FAIL: spatialGIS is not initialized');
  process.exit(1);
}

console.log('  [PASS] spatialGIS initialized with total districts:', Object.keys(spatialGIS.districts).length);

// Test district lookups
const testLocations = [
  'Brahmanbaria',
  'Gazipur, Dhaka',
  'Sirajganj',
  'Jamuna River Corridor',
  'Meghna Bridge, Barishal',
  'Khulna Port Area',
  'Unknown District ABC'
];

testLocations.forEach(loc => {
  const res = spatialGIS.resolveSpatialData(loc);
  if (!res || !res.coordinates || !res.bbox || !res.orbitPass) {
    console.error(`FAIL: Failed to resolve spatial data for "${loc}"`);
    process.exit(1);
  }
  console.log(`  [PASS] Resolved "${loc}" -> Region: "${res.regionName}", Orbit: ${res.orbitPass}, Mean Coherence: ${res.meanCoherence}`);
});

// Load state store
require('./js/state.js');
const tenderStore = window.tenderStore;
if (!tenderStore) {
  console.error('FAIL: tenderStore not initialized');
  process.exit(1);
}

// Subscribe to tenderSelected event
let eventFired = false;
let selectedTenderData = null;

tenderStore.subscribe('tenderSelected', (tender) => {
  eventFired = true;
  selectedTenderData = tender;
  console.log(`  [EVENT] tenderSelected received for Tender #${tender.tenderId}: "${tender.title}"`);
  console.log(`          Budget: BDT ${(tender.numBudget / 10000000).toFixed(2)} Cr, Agency: ${tender.agency}, District: ${tender.district}`);
  console.log(`          SMT Turnover Req: BDT ${tender.smt.rule40TurnoverReqCr} Cr, Liquid Req: BDT ${tender.smt.rule40LiquidityReqCr} Cr`);
  console.log(`          Spatial Sentinel-1 Track: #${tender.spatial.trackNumber}, Center: [${tender.spatial.coordinates.join(', ')}]`);
});

// Test dynamic selection of different tenders
const mockTenders = [
  {
    tenderId: "LGED-2026-BB-0941",
    title: "Construction of 60m RCC Girder Bridge over Titas River in Brahmanbaria",
    estimatedCost: 185000000,
    agency: "LGED",
    location: "Brahmanbaria"
  },
  {
    tenderId: "RHD-2026-GZ-4019",
    title: "4-Lane Elevated Flyover & Approach Embankment in Gazipur Industrial Zone",
    estimatedCost: 650000000,
    agency: "RHD",
    location: "Gazipur"
  },
  {
    tenderId: "BWDB-2026-SJ-1102",
    title: "Jamuna Riverbank Revetment with CC Blocks and Geo-textile in Sirajganj",
    estimatedCost: 420000000,
    agency: "BWDB",
    location: "Sirajganj"
  }
];

mockTenders.forEach((tender, idx) => {
  eventFired = false;
  tenderStore.setSelectedTender(tender);
  if (!eventFired || !selectedTenderData) {
    console.error(`FAIL: Failed to trigger event for tender #${tender.tenderId}`);
    process.exit(1);
  }
  if (selectedTenderData.tenderId !== tender.tenderId) {
    console.error(`FAIL: Selected tender ID mismatch. Expected ${tender.tenderId}, got ${selectedTenderData.tenderId}`);
    process.exit(1);
  }
  if (!selectedTenderData.spatial || !selectedTenderData.smt) {
    console.error(`FAIL: Selected tender missing enriched spatial or SMT clauses`);
    process.exit(1);
  }
});

console.log('\\n[SUCCESS] Node.js test simulation passed 100% cleanly.');
"""

with open("test_runner.js", "w", encoding="utf-8") as f:
    f.write(node_test_script)

try:
    proc = subprocess.run(["node", "test_runner.js"], capture_output=True, text=True, check=True)
    print(proc.stdout)
except subprocess.CalledProcessError as e:
    print("Node.js Test Execution Failed:")
    print(e.stderr)
    print(e.stdout)
    sys.exit(1)
finally:
    if os.path.exists("test_runner.js"):
        os.remove("test_runner.js")

print("\n=============================================================")
print("✨ ALL 4 ARCHITECTURAL DIRECTIVE PILLARS VERIFIED SUCCESSFULLY")
print("=============================================================")
