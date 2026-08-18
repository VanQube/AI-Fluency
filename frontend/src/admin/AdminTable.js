// Shared presentational table for the three admin managers (Customer /
// Shipment / Package) — same row/edit/delete shape across all three, only
// the column list and form differ per entity.
function AdminTable({ columns, rows, onEdit, onDelete }) {
  if (rows.length === 0) {
    return (
      <p className="font-typewriter text-sm text-saul-black/60">
        No records yet.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-sm border border-saul-black/20">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-saul-black/20 bg-saul-cream">
            {columns.map((col) => (
              <th key={col.key} className="px-3 py-2 font-display text-base tracking-wide text-saul-black">
                {col.label}
              </th>
            ))}
            <th className="px-3 py-2" />
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-saul-black/10 last:border-0">
              {columns.map((col) => (
                <td key={col.key} className="px-3 py-2 font-typewriter text-saul-black/90">
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
              <td className="whitespace-nowrap px-3 py-2 text-right">
                <button
                  type="button"
                  onClick={() => onEdit(row)}
                  className="mr-2 text-xs font-typewriter text-saul-teal underline"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => onDelete(row)}
                  className="text-xs font-typewriter text-saul-rust underline"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default AdminTable;
