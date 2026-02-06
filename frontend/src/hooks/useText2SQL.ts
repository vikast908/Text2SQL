import { useMutation } from "@tanstack/react-query";
import { text2sql, Text2SQLRequest, Text2SQLResponse, APIError } from "@/services/api";

/**
 * React Query hook for Text2SQL API calls
 * 
 * @returns Mutation object with mutate function and state
 */
export function useText2SQL() {
  return useMutation<Text2SQLResponse, APIError, Text2SQLRequest>({
    mutationFn: text2sql,
    retry: (failureCount, error) => {
      // Don't retry on client errors (4xx) or if it's a network error that we can't recover from
      if (error.statusCode >= 400 && error.statusCode < 500) {
        return false;
      }
      // Retry up to 2 times for server errors (5xx) or network errors
      return failureCount < 2;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
  });
}
