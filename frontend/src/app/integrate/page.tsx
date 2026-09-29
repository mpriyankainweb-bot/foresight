'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Code2,
  Key,
  Terminal,
  Plus,
} from 'lucide-react';
import { Navbar } from '../../components/Navbar';
import { Card, Badge, Button, CopyButton, ErrorBanner } from '../../components/UIComponents';
import { api, GenerateApiKeyResponse } from '../../lib/api';

export default function IntegratePage() {
  const [keyName, setKeyName] = useState('paynest-prod-ci');
  const [generatedKey, setGeneratedKey] = useState<GenerateApiKeyResponse | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateKey = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const res = await api.generateApiKey(keyName || 'default');
      setGeneratedKey(res);
      if (typeof window !== 'undefined') {
        localStorage.setItem('foresight_api_key', res.api_key);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate API key');
    } finally {
      setIsGenerating(false);
    }
  };

  const activeKeyStr = generatedKey?.api_key || 'foresight-secret-key-123';

  const snippets = {
    curl: `curl -X POST "http://localhost:8000/api/v1/deploys/check" \\
  -H "X-API-Key: ${activeKeyStr}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "service": "payments-gateway",
    "title": "Lower gateway retry timeout from 30s to 8s",
    "config_changes": ["PAYMENT_GATEWAY_RETRY_TIMEOUT_MS=8000"],
    "environment": "production"
  }'`,

    python: `import httpx

api_key = "${activeKeyStr}"
url = "http://localhost:8000/api/v1/deploys/check"

payload = {
    "service": "payments-gateway",
    "title": "Lower gateway retry timeout from 30s to 8s",
    "config_changes": ["PAYMENT_GATEWAY_RETRY_TIMEOUT_MS=8000"],
    "environment": "production"
}

headers = {"X-API-Key": api_key}
response = httpx.post(url, json=payload, headers=headers)
verdict = response.json()

print(f"Verdict: {verdict['verdict']} | Risk Score: {verdict['risk_score']}/100")`,

    javascript: `const API_KEY = '${activeKeyStr}';

async function checkDeploy() {
  const response = await fetch('http://localhost:8000/api/v1/deploys/check', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    },
    body: JSON.stringify({
      service: 'payments-gateway',
      title: 'Lower gateway retry timeout from 30s to 8s',
      config_changes: ['PAYMENT_GATEWAY_RETRY_TIMEOUT_MS=8000'],
      environment: 'production',
    }),
  });

  const data = await response.json();
  console.log('Verdict:', data.verdict, 'Risk Score:', data.risk_score);
}

checkDeploy();`,

    github: `name: Foresight Deploy Guard
on:
  pull_request:
    branches: [main, master]

jobs:
  foresight-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run Foresight Deploy Check
        uses: ./.github/actions/foresight
        with:
          api-key: \${{ secrets.FORESIGHT_API_KEY }}
          service: payments-gateway
          fail-on-hold: "true"`,

    cli: `# Install CLI package locally
pip install -e cli/

# Run safety check for payments-gateway change
foresight check \\
  --service payments-gateway \\
  --title "Lower gateway retry timeout from 30s to 8s" \\
  --diff ./change.diff

# CLI Exit Codes:
# 0 = SHIP
# 1 = CANARY
# 2 = HOLD`,
  };

  return (
    <div className="min-h-screen bg-[#0B0D12] flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#12151C] p-6 rounded-16 border border-[#1F2430]">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-extrabold text-white">Integration Hub</h1>
              <Badge variant="primary">
                <Code2 className="w-3.5 h-3.5 mr-1" /> API & Tooling
              </Badge>
            </div>
            <p className="text-sm text-[#8A90A2]">
              Generate API keys and integrate Foresight into CI/CD pipelines, GitHub Actions, or local CLI workflows.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 space-y-6">
            <Card className="space-y-5">
              <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-[#1F2430] pb-3">
                <Key className="w-4 h-4 text-[#7C5CFF]" />
                API Key Generator
              </h2>

              <div className="space-y-4 text-xs">
                <div>
                  <label className="block text-[#8A90A2] font-medium mb-1">Key Description / Name</label>
                  <input
                    type="text"
                    value={keyName}
                    onChange={(e) => setKeyName(e.target.value)}
                    placeholder="e.g. paynest-ci-pipeline"
                    className="w-full bg-[#0B0D12] border border-[#1F2430] rounded-12 px-3 py-2 text-sm text-white focus:border-[#7C5CFF] focus:outline-none"
                  />
                </div>

                <Button
                  variant="primary"
                  className="w-full gap-2"
                  isLoading={isGenerating}
                  onClick={handleGenerateKey}
                >
                  <Plus className="w-4 h-4" />
                  <span>Generate New X-API-Key</span>
                </Button>
              </div>

              {error && <ErrorBanner message={error} />}

              {generatedKey && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="p-4 bg-[#0B0D12] border border-[#2DD4A0]/40 rounded-12 space-y-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#2DD4A0]">Key Generated Successfully</span>
                    <CopyButton text={generatedKey.api_key} label="Copy Key" />
                  </div>
                  <p className="font-mono text-[#E6E8EE] break-all bg-[#12151C] p-2.5 rounded-8 border border-[#1F2430]">
                    {generatedKey.api_key}
                  </p>
                  <p className="text-[11px] text-[#8A90A2]">
                    Key saved to local browser storage for automatic API authentication.
                  </p>
                </motion.div>
              )}
            </Card>
          </div>

          <div className="lg:col-span-7 space-y-6">
            <Card className="space-y-6">
              <h2 className="text-base font-bold text-white flex items-center gap-2 border-b border-[#1F2430] pb-3">
                <Terminal className="w-4 h-4 text-[#2DD4A0]" />
                Client & Pipeline SDK Examples
              </h2>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-mono text-[#8A90A2]">
                  <span className="text-[#E6E8EE] font-bold">1. REST API (cURL)</span>
                  <CopyButton text={snippets.curl} />
                </div>
                <pre className="bg-[#0B0D12] p-4 rounded-12 border border-[#1F2430] text-xs font-mono text-[#9E85FF] overflow-x-auto">
                  {snippets.curl}
                </pre>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-mono text-[#8A90A2]">
                  <span className="text-[#E6E8EE] font-bold">2. Python Client</span>
                  <CopyButton text={snippets.python} />
                </div>
                <pre className="bg-[#0B0D12] p-4 rounded-12 border border-[#1F2430] text-xs font-mono text-[#2DD4A0] overflow-x-auto">
                  {snippets.python}
                </pre>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-mono text-[#8A90A2]">
                  <span className="text-[#E6E8EE] font-bold">3. JavaScript / Node.js Client</span>
                  <CopyButton text={snippets.javascript} />
                </div>
                <pre className="bg-[#0B0D12] p-4 rounded-12 border border-[#1F2430] text-xs font-mono text-[#38BDF8] overflow-x-auto">
                  {snippets.javascript}
                </pre>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-mono text-[#8A90A2]">
                  <span className="text-[#E6E8EE] font-bold">4. GitHub Action (.github/workflows/foresight.yml)</span>
                  <CopyButton text={snippets.github} />
                </div>
                <pre className="bg-[#0B0D12] p-4 rounded-12 border border-[#1F2430] text-xs font-mono text-[#FFB020] overflow-x-auto">
                  {snippets.github}
                </pre>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-mono text-[#8A90A2]">
                  <span className="text-[#E6E8EE] font-bold">5. Command-Line Interface (foresight check)</span>
                  <CopyButton text={snippets.cli} />
                </div>
                <pre className="bg-[#0B0D12] p-4 rounded-12 border border-[#1F2430] text-xs font-mono text-[#E6E8EE] overflow-x-auto">
                  {snippets.cli}
                </pre>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
