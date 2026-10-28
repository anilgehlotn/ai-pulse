import React, { useState } from "react";
import { Trash2 } from "lucide-react";
import { api } from "../api.js";
import { ErrorBox } from "./Status.jsx";

const CONFIRM_WORD = "DELETE"; // the backend refuses anything else

// "Delete all my answers": opens a confirmation where the user must type DELETE.
export default function DeleteMyData({ onDeleted }) {
  const [open, setOpen] = useState(false);
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  if (!open) {
    return (
      <button type="button" className="danger-outline" onClick={() => setOpen(true)}>
        <Trash2 size={16} aria-hidden="true" />
        Delete all my answers
      </button>
    );
  }

  async function confirmDelete(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await api("/me/data", { method: "DELETE", body: JSON.stringify({ confirm: typed }) });
      onDeleted(result);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  function cancel() {
    setOpen(false);
    setTyped("");
    setError("");
  }

  return (
    <form className="confirm-box" onSubmit={confirmDelete}>
      <p>
        <strong>This deletes every answer you have given, in every organization.</strong> It can't be undone.
        Your account stays, so you can take the diagnostic again.
      </p>
      <label htmlFor="confirm-delete">Type {CONFIRM_WORD} to confirm</label>
      <input id="confirm-delete" value={typed} autoComplete="off" autoFocus onChange={(e) => setTyped(e.target.value)} />
      <ErrorBox message={error} />
      <div className="button-row">
        <button type="submit" className="danger" disabled={typed !== CONFIRM_WORD || busy}>
          {busy ? "Deleting…" : "Delete permanently"}
        </button>
        <button type="button" className="secondary" onClick={cancel}>Cancel</button>
      </div>
    </form>
  );
}
