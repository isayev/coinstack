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

export async function downloadBackup() {
  // Real implementation would be:
  // window.location.href = `${api.defaults.baseURL}/api/v2/settings/backup`;
  console.log("Downloading backup...");
}

export async function downloadCSV() {
  // Real implementation would be:
  // window.location.href = `${api.defaults.baseURL}/api/v2/settings/export-csv`;
  console.log("Downloading CSV...");
}