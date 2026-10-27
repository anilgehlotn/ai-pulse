import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";

// Loads one GET endpoint. Returns {data, error, loading, reload}.
export function useApi(path) {
  const [state, setState] = useState({ data: null, error: "", loading: true });

  const reload = useCallback(() => {
    setState((s) => ({ ...s, error: "", loading: true }));
    return api(path)
      .then((data) => setState({ data, error: "", loading: false }))
      .catch((err) => setState({ data: null, error: err.message, loading: false }));
  }, [path]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { ...state, reload };
}
