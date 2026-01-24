import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface DatabaseInfo {
  size_mb: number;
  coin_count: number;
  last_modified: string;
  path: string;
}

export function useDatabaseInfo() {
  return useQuery({
    queryKey: ["database-info"],
    queryFn: async () => {
      const response = await api.get<DatabaseInfo>("/api/settings/database-info");
      return response.data;
    },
  });
}

export function downloadBackup() {
  window.open("/api/settings/backup", "_blank");
}

export function downloadCSV() {
  window.open("/api/settings/export-csv", "_blank");
}
