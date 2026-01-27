import { useQuery } from "@tanstack/react-query";


export interface DatabaseInfo {
  coin_count: number;
  size_mb: number;
  last_modified: string;
}

export function useDatabaseInfo() {
  return useQuery({
    queryKey: ["database-info"],
    queryFn: async () => {
      // Mock for now until backend endpoint exists
      // Real: const response = await api.get<DatabaseInfo>("/api/v2/settings/db-info");
      // return response.data;

      return {
        coin_count: 110,
        size_mb: 0.5,
        last_modified: new Date().toLocaleString()
      };
    }
  });
}

/**
 * STUB: Download database backup
 * TODO: Implement /api/v2/settings/backup endpoint
 */
export async function downloadBackup() {
  // Real implementation would be:
  // window.location.href = `${api.defaults.baseURL}/api/v2/settings/backup`;
  if (import.meta.env.DEV) {
    console.log("STUB: downloadBackup - not implemented");
  }
}

/**
 * STUB: Download CSV export
 * TODO: Implement /api/v2/settings/export-csv endpoint
 */
export async function downloadCSV() {
  // Real implementation would be:
  // window.location.href = `${api.defaults.baseURL}/api/v2/settings/export-csv`;
  if (import.meta.env.DEV) {
    console.log("STUB: downloadCSV - not implemented");
  }
}