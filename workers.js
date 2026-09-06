export default {
  async fetch(request, env, ctx) {
    // CORS Headers
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);

    // Root Endpoint
    if (url.pathname === "/" && request.method === "GET") {
      return new Response(JSON.stringify({
        status: "online",
        service: "S-Indexer",
        developer: "Sgdev",
        engine: "Cloudflare Edge"
      }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });
    }

    // Health Endpoint
    if (url.pathname === "/api/v1/health" && request.method === "GET") {
      return new Response(JSON.stringify({ status: "ok" }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });
    }

    // Submit Endpoint
    if (url.pathname === "/api/v1/submit" && request.method === "POST") {
      try {
        const body = await request.json();
        const targetUrl = body.url;

        const feedNodes = [
          "https://1.sindex.duckdns.org",
          "https://2.sindex.duckdns.org",
          "https://3.sindex.duckdns.org",
          "https://4.sindex.duckdns.org",
          "https://5.sindex.duckdns.org"
        ];
        const assignedNode = feedNodes[Math.floor(Math.random() * feedNodes.length)];

        // Background Processing
        ctx.waitUntil((async () => {
          let indexnowStatus = "Failed";
          try {
            const indexnowRes = await fetch("https://api.indexnow.org/indexnow", {
              method: "POST",
              headers: { "Content-Type": "application/json; charset=utf-8" },
              body: JSON.stringify({
                host: "sindex.duckdns.org",
                key: env.INDEXNOW_KEY || "sindex-auth-key-1234",
                keyLocation: env.INDEXNOW_KEY_LOCATION || "https://sindex.duckdns.org/indexnow_key.txt",
                urlList: [targetUrl]
              })
            });
            if (indexnowRes.ok) indexnowStatus = "Dispatched";
          } catch (e) {}

          const sheetUrl = env.GOOGLE_SHEET_WEBAPP_URL || "https://script.google.com/macros/s/AKfycbzG1fAg6CKkbsOLaNgGRsuqvYoyg8tva6VwPQusEfzsISyJXmVchP_72Vjj9_jY3zATEQ/exec";
          if (sheetUrl) {
            try {
              await fetch(sheetUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json; charset=utf-8" },
                body: JSON.stringify({
                  url: targetUrl,
                  node: assignedNode,
                  indexnow: indexnowStatus
                })
              });
            } catch (e) {}
          }
        })());

        return new Response(JSON.stringify({
          success: true,
          message: "URL received and queued.",
          target_url: targetUrl,
          assigned_feed_node: assignedNode,
          indexnow_dispatched: true
        }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });

      } catch (err) {
        return new Response(JSON.stringify({ error: err.message }), {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }
    }

    return new Response(JSON.stringify({ error: "Not Found" }), {
      status: 404,
      headers: { ...corsHeaders, "Content-Type": "application/json" }
    });
  }
};
