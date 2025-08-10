import { getHeaders, handleApiError } from './authUtils';
import { FileUploadResponse, FileDeleteResponse, FileHistoryEntry } from './api';
import { authApi } from './api';

class FileApi {
  private baseUrl = 'http://127.0.0.1:8000/leads/files';

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    let headers: HeadersInit = getHeaders();
    if (options.body instanceof FormData) {
      delete headers['Content-Type'];
    }

    return handleApiError(async () => {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: { ...headers, ...options.headers },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'API request failed');
      }

      return response.json();
    });
  }

  async uploadFile(
    file: File,
    options?: {
      sheet_name?: string;
      encoding?: string;
      delimiter?: string;
    }
  ): Promise<FileUploadResponse> {
    const userId = await authApi.getUserId();
    const formData = new FormData();
    formData.append('file', file);

    const queryParams = new URLSearchParams();
    if (options?.sheet_name) queryParams.append('sheet_name', options.sheet_name);
    if (options?.encoding) queryParams.append('encoding', options.encoding);
    if (options?.delimiter) queryParams.append('delimiter', options.delimiter);

    return this.request<FileUploadResponse>(
      `/upload?${queryParams.toString()}`,
      {
        method: 'POST',
        body: formData,
      }
    );
  }

  async getFileHistory(limit: number = 50, offset: number = 0): Promise<FileHistoryEntry[]> {
    const userId = await authApi.getUserId();
    return this.request<FileHistoryEntry[]>(`/${userId}/history?limit=${limit}&offset=${offset}`);
  }

  async deleteFile(fileId: number): Promise<FileDeleteResponse> {
    const userId = await authApi.getUserId();
    return this.request<FileDeleteResponse>(`/${userId}/${fileId}`, {
      method: 'DELETE',
    });
  }
}

export const fileApi = new FileApi();