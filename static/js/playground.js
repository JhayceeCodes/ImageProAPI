(() => {
    const uploadForm = document.getElementById("upload-form");
    const resetUploadFormButton = document.getElementById("reset-upload-form");
    const playgroundAuthSummary = document.getElementById("playground-auth-summary");
    const playgroundAuthActions = document.getElementById("playground-auth-actions");
    const operationsPreview = document.getElementById("operations-preview");
    const operationCount = document.getElementById("operation-count");
    const responseStatus = document.getElementById("response-status");
    const responsePreview = document.getElementById("response-preview");
    const htmlPreviewActions = document.getElementById("html-preview-actions");
    const toggleHtmlPreviewButton = document.getElementById("toggle-html-preview");
    const htmlResponseContainer = document.getElementById("html-response-container");
    const htmlResponseFrame = document.getElementById("html-response-frame");
    const pollJobStatusButton = document.getElementById("poll-job-status");
    const jobStatusBadge = document.getElementById("job-status-badge");
    const jobSummary = document.getElementById("job-summary");
    const jobImageId = document.getElementById("job-image-id");
    const jobDetailUrl = document.getElementById("job-detail-url");
    const jobDownloadUrl = document.getElementById("job-download-url");
    const imagePreviewContainer = document.getElementById("image-preview-container");
    const imagePreview = document.getElementById("image-preview");
    const downloadImageLink = document.getElementById("download-image-link");

    if (!uploadForm) {
        return;
    }

    const uploadFields = {
        originalImage: document.getElementById("original-image"),
        enableResize: document.getElementById("enable-resize"),
        resizeWidth: document.getElementById("resize-width"),
        resizeHeight: document.getElementById("resize-height"),
        enableCompress: document.getElementById("enable-compress"),
        compressQuality: document.getElementById("compress-quality"),
        enableFilter: document.getElementById("enable-filter"),
        filterType: document.getElementById("filter-type"),
        enableConvert: document.getElementById("enable-convert"),
        convertFormat: document.getElementById("convert-format"),
    };

    const jobState = {
        id: null,
        detailUrl: null,
        downloadUrl: null,
        previewObjectUrl: null,
    };

    function setResponseState(message, kind) {
        responseStatus.classList.remove(
            "hidden",
            "bg-red-50",
            "text-red-700",
            "bg-emerald-50",
            "text-emerald-700",
            "bg-amber-50",
            "text-amber-700"
        );

        if (kind === "error") {
            responseStatus.classList.add("bg-red-50", "text-red-700");
        } else if (kind === "warning") {
            responseStatus.classList.add("bg-amber-50", "text-amber-700");
        } else {
            responseStatus.classList.add("bg-emerald-50", "text-emerald-700");
        }

        responseStatus.textContent = message;
    }

    function summarizeHtmlDocument(html) {
        const doc = new DOMParser().parseFromString(html, "text/html");
        const title = doc.querySelector("title")?.textContent?.trim();
        const heading = doc.querySelector("h1, h2, h3")?.textContent?.trim();
        const bodyText = (doc.body?.innerText || "")
            .replace(/\s+/g, " ")
            .trim()
            .slice(0, 600);

        return {
            title: title || "HTML response received",
            heading: heading || "",
            bodyText: bodyText || "The server returned an HTML document instead of a JSON API response.",
        };
    }

    function clearPreviewObjectUrl() {
        if (jobState.previewObjectUrl) {
            URL.revokeObjectURL(jobState.previewObjectUrl);
            jobState.previewObjectUrl = null;
        }
    }

    function resetJobState() {
        clearPreviewObjectUrl();
        jobState.id = null;
        jobState.detailUrl = null;
        jobState.downloadUrl = null;
        jobStatusBadge.textContent = "No job yet";
        jobStatusBadge.className = "rounded-md bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600";
        jobSummary.textContent = "Submit an upload to populate the job details, poll processing status, and preview the finished image.";
        jobImageId.textContent = "-";
        jobDetailUrl.textContent = "-";
        jobDownloadUrl.textContent = "-";
        imagePreviewContainer.classList.add("hidden");
        imagePreview.removeAttribute("src");
        downloadImageLink.classList.add("hidden");
        downloadImageLink.removeAttribute("href");
    }

    function setJobBadge(status) {
        const classes = {
            pending: "rounded-md bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700",
            processing: "rounded-md bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700",
            completed: "rounded-md bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700",
            failed: "rounded-md bg-red-50 px-3 py-1 text-xs font-semibold text-red-700",
        };

        jobStatusBadge.textContent = status || "unknown";
        jobStatusBadge.className = classes[status] || "rounded-md bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600";
    }

    function normalizeUrl(url) {
        if (!url) {
            return null;
        }
        try {
            return new URL(url, window.location.origin).toString();
        } catch (_) {
            return url;
        }
    }

    function buildOperations() {
        const operations = [];

        if (uploadFields.enableResize.checked) {
            const width = Number(uploadFields.resizeWidth.value);
            const height = Number(uploadFields.resizeHeight.value);
            if (width > 0 && height > 0) {
                operations.push({
                    operation_type: "resize",
                    parameters: { width, height },
                });
            }
        }

        if (uploadFields.enableCompress.checked) {
            const quality = Number(uploadFields.compressQuality.value);
            if (quality > 0) {
                operations.push({
                    operation_type: "compress",
                    parameters: { quality },
                });
            }
        }

        if (uploadFields.enableFilter.checked && uploadFields.filterType.value) {
            operations.push({
                operation_type: "filter",
                parameters: { type: uploadFields.filterType.value },
            });
        }

        if (uploadFields.enableConvert.checked && uploadFields.convertFormat.value) {
            operations.push({
                operation_type: "convert",
                parameters: { format: uploadFields.convertFormat.value },
            });
        }

        return operations;
    }

    function updateOperationsPreview() {
        const operations = buildOperations();
        operationsPreview.textContent = JSON.stringify(operations, null, 2);
        operationCount.textContent = `${operations.length} operation${operations.length === 1 ? "" : "s"}`;
        return operations;
    }

    async function readResponseBody(response) {
        const contentType = response.headers.get("content-type") || "";

        if (contentType.includes("application/json")) {
            return {
                kind: "json",
                body: await response.json(),
            };
        }

        const text = await response.text();
        if (contentType.includes("text/html")) {
            return {
                kind: "html",
                body: text,
            };
        }

        return {
            kind: "text",
            body: text,
        };
    }

    function showResponsePayload(result) {
        htmlPreviewActions.classList.add("hidden");
        htmlResponseContainer.classList.add("hidden");
        htmlResponseFrame.srcdoc = "";
        toggleHtmlPreviewButton.textContent = "Preview HTML response";

        if (result.kind === "json") {
            responsePreview.textContent = JSON.stringify(result.body, null, 2);
            return;
        }

        if (result.kind === "html") {
            const summary = summarizeHtmlDocument(result.body);
            responsePreview.textContent = [
                "HTML response received",
                `Title: ${summary.title}`,
                summary.heading ? `Heading: ${summary.heading}` : null,
                "",
                summary.bodyText,
            ].filter(Boolean).join("\n");
            htmlResponseFrame.srcdoc = result.body;
            htmlPreviewActions.classList.remove("hidden");
            setResponseState("Received an HTML response. Use the preview button to inspect the full document.", "warning");
            return;
        }

        responsePreview.textContent = result.body;
    }

    async function submitJsonForm(url, payload, successMessage, onSuccess) {
        responsePreview.textContent = "Submitting request...";
        responseStatus.classList.add("hidden");

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            const result = await readResponseBody(response);
            showResponsePayload(result);

            if (!response.ok) {
                if (result.kind !== "html") {
                    setResponseState(`Request failed with status ${response.status}.`, "error");
                }
                return;
            }

            setResponseState(successMessage, "success");
            if (onSuccess) {
                onSuccess(result.body);
            }
        } catch (error) {
            responsePreview.textContent = String(error);
            setResponseState("Network error while calling the authentication endpoint.", "error");
        }
    }

    async function fetchPreviewImage() {
        if (!jobState.downloadUrl) {
            return;
        }

        try {
            const response = await window.ImageProAuth.authorizedFetch(jobState.downloadUrl);

            if (!response.ok) {
                setResponseState("The image is marked complete, but downloading the preview failed.", "warning");
                return;
            }

            const blob = await response.blob();
            clearPreviewObjectUrl();
            jobState.previewObjectUrl = URL.createObjectURL(blob);
            imagePreview.src = jobState.previewObjectUrl;
            imagePreviewContainer.classList.remove("hidden");
            downloadImageLink.href = jobState.previewObjectUrl;
            downloadImageLink.download = `processed-image.${blob.type.split("/")[1] || "bin"}`;
            downloadImageLink.classList.remove("hidden");
        } catch (_) {
            setResponseState("The image is ready, but the preview request failed.", "warning");
        }
    }

    async function syncJobResult(detailUrlOverride) {
        const targetUrl = normalizeUrl(detailUrlOverride || jobState.detailUrl);
        if (!targetUrl) {
            setResponseState("There is no detail URL available for polling yet.", "error");
            return;
        }

        jobState.detailUrl = targetUrl;
        jobDetailUrl.textContent = targetUrl;

        try {
            const response = await window.ImageProAuth.authorizedFetch(targetUrl);
            const result = await readResponseBody(response);
            showResponsePayload(result);

            if (!response.ok) {
                if (result.kind !== "html") {
                    setResponseState(`Polling failed with status ${response.status}.`, "error");
                }
                return;
            }

            if (result.kind !== "json" || !result.body) {
                setResponseState("Detail polling did not return the expected JSON payload.", "warning");
                return;
            }

            const body = result.body;
            jobState.id = body.id || jobState.id;
            jobState.downloadUrl = normalizeUrl(body.download_url);
            jobImageId.textContent = jobState.id || "-";
            jobDownloadUrl.textContent = jobState.downloadUrl || "-";
            setJobBadge(body.status);

            if (body.status === "completed" && jobState.downloadUrl) {
                jobSummary.textContent = "The image has finished processing. Preview and download are now available.";
                await fetchPreviewImage();
            } else if (body.status === "processing") {
                clearPreviewObjectUrl();
                imagePreviewContainer.classList.add("hidden");
                downloadImageLink.classList.add("hidden");
                jobSummary.textContent = body.seconds_remaining != null
                    ? `The image is still processing. Estimated time remaining: ${body.seconds_remaining} seconds.`
                    : "The image is still processing.";
            } else if (body.status === "pending") {
                clearPreviewObjectUrl();
                imagePreviewContainer.classList.add("hidden");
                downloadImageLink.classList.add("hidden");
                jobSummary.textContent = "The upload has been accepted and is waiting to be processed.";
            } else if (body.status === "failed") {
                clearPreviewObjectUrl();
                imagePreviewContainer.classList.add("hidden");
                downloadImageLink.classList.add("hidden");
                jobSummary.textContent = "The image job failed during processing.";
            }

            setResponseState(`Job status updated: ${body.status}.`, body.status === "failed" ? "error" : "success");
        } catch (error) {
            responsePreview.textContent = String(error);
            setResponseState("Network error while polling the image detail endpoint.", "error");
        }
    }

    function updatePlaygroundAuthSummary() {
        const auth = window.ImageProAuth.readStoredAuth();
        if (auth && auth.access) {
            playgroundAuthSummary.textContent = "You are signed in. The playground will automatically attach your saved access token and refresh it when needed.";
            playgroundAuthActions.classList.add("hidden");
            return;
        }
        playgroundAuthSummary.textContent = "You are currently using the anonymous flow. Log in from the main app navigation to use saved tokens here automatically.";
        playgroundAuthActions.classList.remove("hidden");
    }

    function bindFormListeners() {
        Object.values(uploadFields).forEach((element) => {
            element.addEventListener("input", updateOperationsPreview);
            element.addEventListener("change", updateOperationsPreview);
        });

        uploadForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            if (!uploadFields.originalImage.files.length) {
                setResponseState("Choose an image file before submitting the upload request.", "error");
                return;
            }

            const operations = updateOperationsPreview();
            const formData = new FormData();
            formData.append("original_image", uploadFields.originalImage.files[0]);
            formData.append("operations", JSON.stringify(operations));

            responsePreview.textContent = "Submitting request...";
            responseStatus.classList.add("hidden");

            try {
                const response = await window.ImageProAuth.authorizedFetch("/api/images/", {
                    method: "POST",
                    body: formData,
                });

                const result = await readResponseBody(response);
                showResponsePayload(result);

                if (!response.ok) {
                    if (result.kind !== "html") {
                        setResponseState(`Upload failed with status ${response.status}.`, "error");
                    }
                    return;
                }

                if (result.kind === "json" && result.body) {
                    jobState.id = result.body.id || null;
                    jobState.detailUrl = normalizeUrl(result.body.detail_url);
                    jobState.downloadUrl = null;
                    jobImageId.textContent = jobState.id || "-";
                    jobDetailUrl.textContent = jobState.detailUrl || "-";
                    jobDownloadUrl.textContent = "-";
                    setJobBadge(result.body.status || "pending");
                    jobSummary.textContent = "Upload request accepted. Poll the job status to track processing and unlock preview/download.";
                    setResponseState("Upload request accepted. Use the job result panel to poll status.", "success");
                    await syncJobResult(jobState.detailUrl);
                    return;
                }

                setResponseState("Upload request accepted.", "success");
            } catch (error) {
                responsePreview.textContent = String(error);
                setResponseState("Network error while calling /api/images/.", "error");
            }
        });

        resetUploadFormButton.addEventListener("click", () => {
            uploadForm.reset();
            updateOperationsPreview();
            htmlPreviewActions.classList.add("hidden");
            htmlResponseContainer.classList.add("hidden");
            htmlResponseFrame.srcdoc = "";
            resetJobState();
        });

        toggleHtmlPreviewButton.addEventListener("click", () => {
            const isHidden = htmlResponseContainer.classList.contains("hidden");
            htmlResponseContainer.classList.toggle("hidden");
            toggleHtmlPreviewButton.textContent = isHidden
                ? "Hide HTML preview"
                : "Preview HTML response";
        });

        pollJobStatusButton.addEventListener("click", async () => {
            await syncJobResult();
        });
    }

    function initPlayground() {
        bindFormListeners();
        resetJobState();
        updatePlaygroundAuthSummary();
        updateOperationsPreview();
    }

    initPlayground();
})();
