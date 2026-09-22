/*
 * houdini-relay — GitHub Pages 版の「AI に聞く」から Gemini を呼ぶための中継。
 *
 * 鍵（GEMINI_API_KEY）はこの Worker の Secret にだけ置く。ページには一切出さない。
 * 呼び出し元は site/partial_chrome.html の relaySample()。
 *
 * 入力: POST { "messages": [{role:"user"|"assistant", content:"..."}, ...] }
 *   messages[0] はサイト側のルール文（システム指示）で固定。
 * 出力（成功）: 200 { "text": "...", "truncated": false }
 * 出力（失敗）: 4xx/5xx { "code": "...", "message": "..." }
 *   code は partial_chrome.html 側が知っている文字列に合わせる:
 *   rate_limited / refused / empty_completion / prompt_too_large / upstream_error
 *
 * 環境変数（Cloudflare の Settings → Variables and Secrets）:
 *   GEMINI_API_KEY  … Secret。Google AI Studio で発行した鍵
 *   GEMINI_MODEL    … 通常の変数。既定は下の DEFAULT_MODEL。
 *                     動かないときは ListModels で確かめて変える（下のコメント参照）
 *
 * 注意（確かめていないこと）:
 *   DEFAULT_MODEL は 2026年1月頃の知識に基づく名前で、今も使えるかは確認していない。
 *   動かなければ、鍵を使って次を叩き、返ってきた名前のどれかを GEMINI_MODEL に設定する:
 *     curl "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY"
 *
 * 注意（この仕組みの限界）:
 *   ORIGIN のチェックはブラウザの CORS を通す・通さないだけで、curl 等の
 *   サーバー間呼び出しは Origin ヘッダを自由に偽れるため、これは「鍵を隠す」
 *   ためのものであって「他人に使わせない」ための強い仕組みではない。
 *   悪用が増えたら、質問欄に合言葉を1つ挟むなどの追加が要る（未着手）。
 */

const DEFAULT_MODEL = "gemini-3.6-flash"; // ユーザー指定（2026-09-22）。API での正式な id は未確認

// GitHub Pages と、手元で docs/ を試すときのローカルサーバー。
// 増やすときはここに足す。
const ALLOW_ORIGINS = new Set([
  "https://realestatewarrior.github.io",
  "http://localhost:8765",
]);

const MAX_INPUT_CHARS = 20000; // これを超えたら Gemini を呼ばずに断る

function corsHeaders(origin) {
  const headers = {
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
  if (origin && ALLOW_ORIGINS.has(origin)) {
    headers["Access-Control-Allow-Origin"] = origin;
  }
  return headers;
}

function json(status, body, origin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders(origin) },
  });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }
    if (request.method !== "POST") {
      return json(405, { code: "upstream_error", message: "POST だけ受け付けます" }, origin);
    }
    // ブラウザ以外（Origin なし）や許可外のサイトからは弾く。
    // 完全な防御ではない（上の注意を参照）が、素通しは避ける。
    if (!origin || !ALLOW_ORIGINS.has(origin)) {
      return json(403, { code: "upstream_error", message: "許可されていない呼び出し元です" }, origin);
    }
    if (!env.GEMINI_API_KEY) {
      return json(500, { code: "upstream_error", message: "鍵が設定されていません" }, origin);
    }

    let body;
    try {
      body = await request.json();
    } catch (e) {
      return json(400, { code: "upstream_error", message: "JSON が壊れています" }, origin);
    }
    const messages = Array.isArray(body && body.messages) ? body.messages : [];
    if (!messages.length) {
      return json(400, { code: "upstream_error", message: "messages が空です" }, origin);
    }

    const totalChars = messages.reduce((n, m) => n + String(m.content || "").length, 0);
    if (totalChars > MAX_INPUT_CHARS) {
      return json(400, { code: "prompt_too_large", message: "質問が長すぎます" }, origin);
    }

    // messages[0] をシステム指示に、残りを会話に振り分ける。
    const [system, ...rest] = messages;
    const contents = rest.map((m) => ({
      role: m.role === "assistant" ? "model" : "user",
      parts: [{ text: String(m.content || "") }],
    }));

    const model = env.GEMINI_MODEL || DEFAULT_MODEL;
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${env.GEMINI_API_KEY}`;

    let upstream;
    try {
      upstream = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: String((system && system.content) || "") }] },
          contents,
          generationConfig: { maxOutputTokens: 1024 },
        }),
      });
    } catch (e) {
      return json(502, { code: "upstream_error", message: "Gemini に届きませんでした" }, origin);
    }

    if (upstream.status === 429) {
      return json(429, { code: "rate_limited", message: "混み合っています" }, origin);
    }
    if (!upstream.ok) {
      const text = await upstream.text().catch(() => "");
      return json(502, { code: "upstream_error", message: `Gemini エラー: ${upstream.status} ${text.slice(0, 200)}` }, origin);
    }

    let data;
    try {
      data = await upstream.json();
    } catch (e) {
      return json(502, { code: "upstream_error", message: "Gemini の応答が JSON でない" }, origin);
    }

    const candidate = data.candidates && data.candidates[0];
    if (!candidate) {
      // プロンプトそのものが安全性フィルタで止められた場合もここに来る
      return json(200, { code: "refused", message: "答えられませんでした" }, origin);
    }
    if (candidate.finishReason === "SAFETY" || candidate.finishReason === "RECITATION") {
      return json(200, { code: "refused", message: "答えられませんでした" }, origin);
    }
    const parts = (candidate.content && candidate.content.parts) || [];
    const text = parts.map((p) => p.text || "").join("");
    if (!text) {
      return json(200, { code: "empty_completion", message: "答えが空でした" }, origin);
    }

    return json(200, { text, truncated: candidate.finishReason === "MAX_TOKENS" }, origin);
  },
};
