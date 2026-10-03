// Third Party
import Cookies from "js-cookie";
import createClient from "openapi-fetch";

import type { paths } from "@/Api/OpenApi";

// Base openapi-fetch client with CSRF token interceptor
export const apiClient = createClient<paths>({
  baseUrl: "/",
  credentials: "same-origin",
});

apiClient.use({
  async onRequest({ request }) {
    const csrf = Cookies.get("csrftoken");
    if (csrf) {
      request.headers.set("X-CSRFToken", csrf);
    }
    return request;
  },
});
