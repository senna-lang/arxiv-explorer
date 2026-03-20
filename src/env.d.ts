/// <reference path="../.astro/types.d.ts" />
/// <reference types="@cloudflare/workers-types" />

declare namespace Cloudflare {
  interface Env {
    RATINGS_KV: KVNamespace;
  }
}

declare namespace App {
  interface Locals {
    runtime: {
      env: Cloudflare.Env;
    };
  }
}
