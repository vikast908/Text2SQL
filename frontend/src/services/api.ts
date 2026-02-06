/**
 * API service layer for Text2SQL endpoints
 */

// API Response Types
export interface Text2SQLRequest {
  input_text: string;
  max_iterations?: number;
  metadata_path?: string | null;
}

export interface Text2SQLResponse {
  success: boolean;
  sql_query: string;
  data: Array<Record<string, any>>;
  summary: string;
  followup_questions: string[];
  chart?: string | null;
  metadata?: string | null;
}

export interface APIErrorResponse {
  error: string;
  error_code?: string;
  details?: any;
}

/**
 * Custom error class for API errors
 */
export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public errorCode?: string,
    public details?: any
  ) {
    super(message);
    this.name = "APIError";
  }
}

/**
 * Makes a POST request to the Text2SQL API endpoint
 * 
 * @param request - The request payload
 * @returns Promise resolving to the API response
 * @throws APIError if the request fails
 */
export async function text2sql(request: Text2SQLRequest): Promise<Text2SQLResponse> {
  try {
    const response = await fetch("/api/text2sql_lg_code/text2sql", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        input_text: request.input_text,
        max_iterations: request.max_iterations ?? 3,
        metadata_path: request.metadata_path ?? null,
      }),
    });

    // Handle non-OK responses
    if (!response.ok) {
      let errorData: APIErrorResponse;
      try {
        errorData = await response.json();
      } catch {
        // If response is not JSON, create a generic error
        errorData = {
          error: `Request failed with status ${response.status}`,
          error_code: `HTTP_${response.status}`,
        };
      }

      throw new APIError(
        errorData.error || `Request failed with status ${response.status}`,
        response.status,
        errorData.error_code,
        errorData.details
      );
    }

    // Parse successful response
    const data: Text2SQLResponse = await response.json();
    return data;
  } catch (error) {
    // Handle network errors or other exceptions
    if (error instanceof APIError) {
      throw error;
    }

    // Network or other errors
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new APIError(
        "Network error: Unable to connect to the server. Please check your connection.",
        0,
        "NETWORK_ERROR"
      );
    }

    throw new APIError(
      error instanceof Error ? error.message : "An unexpected error occurred",
      0,
      "UNKNOWN_ERROR"
    );
  }
}
