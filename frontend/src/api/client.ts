import type {
    APIPath,
    EntryInput,
    EntryOutput,
    EntriesResponse,
    EntryResponse,
    GetEntriesResponse,
    AddEntryResponse,
    AddEntryValidationError,
} from "./schema-util";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// 共通fetchラッパー
async function fetchApi<T>(path: APIPath, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE_URL}${path}`, options);
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        let errorBody;
        try {
            errorBody = await res.json();
        } catch (jsonErr) {
            const rawText = await res.text();
            errorBody = {
                status: res.status,
                statusText: res.statusText,
                body: rawText,
            };
        }
        throw errorBody;
    }
    return res.json();
}

// エントリー一覧取得
export async function getEntries(): Promise<GetEntriesResponse> {
    return fetchApi<GetEntriesResponse>("/entries", { method: "GET" });
}

// エントリー追加
export async function addEntry(entry: EntryInput): Promise<AddEntryResponse> {
    return fetchApi<AddEntryResponse>("/entries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(entry),
    });
}
