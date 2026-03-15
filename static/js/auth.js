(function () {
    const STORAGE_KEY = "imagepro_auth";

    function readStoredAuth() {
        try {
            const raw = window.localStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (_) {
            return null;
        }
    }

    function writeStoredAuth(data) {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
        updateAuthUi();
    }

    function clearStoredAuth() {
        window.localStorage.removeItem(STORAGE_KEY);
        updateAuthUi();
    }

    function decodeJwt(token) {
        try {
            const payload = token.split(".")[1];
            return JSON.parse(window.atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
        } catch (_) {
            return null;
        }
    }

    function isExpired(token, skewSeconds) {
        const payload = decodeJwt(token);
        if (!payload || !payload.exp) {
            return true;
        }
        const now = Math.floor(Date.now() / 1000);
        return payload.exp <= now + (skewSeconds || 0);
    }

    async function refreshAccessToken() {
        const auth = readStoredAuth();
        if (!auth || !auth.refresh || isExpired(auth.refresh, 0)) {
            clearStoredAuth();
            return null;
        }

        const response = await fetch("/accounts/refresh/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                refresh: auth.refresh,
            }),
        });

        if (!response.ok) {
            clearStoredAuth();
            return null;
        }

        const payload = await response.json();
        const updated = {
            access: payload.access,
            refresh: payload.refresh || auth.refresh,
        };
        writeStoredAuth(updated);
        return updated.access;
    }

    async function getValidAccessToken() {
        const auth = readStoredAuth();
        if (!auth || !auth.access) {
            return null;
        }

        if (!isExpired(auth.access, 30)) {
            return auth.access;
        }

        return refreshAccessToken();
    }

    async function authorizedFetch(url, options) {
        const requestOptions = { ...(options || {}) };
        requestOptions.headers = new Headers(requestOptions.headers || {});

        const access = await getValidAccessToken();
        if (access) {
            requestOptions.headers.set("Authorization", `Bearer ${access}`);
        }

        let response = await fetch(url, requestOptions);

        if (response.status === 401) {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                requestOptions.headers.set("Authorization", `Bearer ${refreshed}`);
                response = await fetch(url, requestOptions);
            }
        }

        return response;
    }

    async function logout() {
        const auth = readStoredAuth();
        if (auth && auth.refresh) {
            try {
                await fetch("/accounts/logout/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        refresh: auth.refresh,
                    }),
                });
            } catch (_) {
            }
        }
        clearStoredAuth();
    }

    function updateAuthUi() {
        const auth = readStoredAuth();
        const isLoggedIn = !!(auth && auth.access);

        document.querySelectorAll('[data-auth="logged-out"]').forEach((element) => {
            element.classList.toggle("hidden", isLoggedIn);
        });

        document.querySelectorAll('[data-auth="logged-in"]').forEach((element) => {
            element.classList.toggle("hidden", !isLoggedIn);
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        updateAuthUi();
        const logoutButton = document.getElementById("logout-button");
        if (logoutButton) {
            logoutButton.addEventListener("click", async () => {
                await logout();
                if (window.location.pathname === "/playground/") {
                    window.location.reload();
                    return;
                }
                window.location.href = "/";
            });
        }
    });

    window.ImageProAuth = {
        readStoredAuth,
        writeStoredAuth,
        clearStoredAuth,
        getValidAccessToken,
        authorizedFetch,
        logout,
        updateAuthUi,
    };
})();
