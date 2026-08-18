import { useState } from 'react';
import {
  useListPackages,
  useCreatePackage,
  useUpdatePackage,
  useDeletePackage,
  useListShipments,
} from '../api/generated/secureship';
import AdminTable from './AdminTable';
import { authFetch } from './authFetch';

const EMPTY_FORM = { shipment_id: '', description: '', weight_kg: '', declared_value: '' };

function PackageManager({ token }) {
  const { data, refetch, isLoading } = useListPackages({ fetch: authFetch(token) });
  const { data: shipmentsData } = useListShipments({ fetch: authFetch(token) });
  const createPackage = useCreatePackage({ fetch: authFetch(token) });
  const updatePackage = useUpdatePackage({ fetch: authFetch(token) });
  const deletePackage = useDeletePackage({ fetch: authFetch(token) });

  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);

  const packages = data?.data ?? [];
  const shipments = shipmentsData?.data ?? [];
  const trackingNumber = (id) => shipments.find((s) => s.id === id)?.tracking_number ?? id;

  const columns = [
    { key: 'description', label: 'Description' },
    { key: 'shipment_id', label: 'Shipment', render: (row) => trackingNumber(row.shipment_id) },
    { key: 'weight_kg', label: 'Weight (kg)' },
    { key: 'declared_value', label: 'Declared value' },
  ];

  function startEdit(pkg) {
    setEditingId(pkg.id);
    setForm({
      shipment_id: pkg.shipment_id,
      description: pkg.description,
      weight_kg: pkg.weight_kg,
      declared_value: pkg.declared_value,
    });
    setError(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setError(null);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);

    if (!form.shipment_id) {
      setError('Pick a shipment.');
      return;
    }

    const result = editingId
      ? await updatePackage.mutateAsync({ packageId: editingId, data: form })
      : await createPackage.mutateAsync({ data: form });

    if (result.status !== 200 && result.status !== 201) {
      setError('Save failed — check the fields and try again.');
      return;
    }
    await refetch();
    cancelEdit();
  }

  async function handleDelete(pkg) {
    setError(null);
    const result = await deletePackage.mutateAsync({ packageId: pkg.id });
    if (result.status !== 204) {
      setError('Could not delete — try again.');
      return;
    }
    await refetch();
  }

  const isSaving = createPackage.isPending || updatePackage.isPending;

  return (
    <div>
      <form
        onSubmit={handleSubmit}
        className="mb-6 grid grid-cols-2 gap-3 rounded-sm border border-saul-black/20 bg-white p-4"
      >
        <h3 className="col-span-2 font-display text-xl tracking-wide text-saul-black">
          {editingId ? 'Edit package' : 'New package'}
        </h3>
        <select
          required
          value={form.shipment_id}
          onChange={(e) => setForm({ ...form, shipment_id: e.target.value })}
          className="col-span-2 rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        >
          <option value="">Select shipment…</option>
          {shipments.map((s) => (
            <option key={s.id} value={s.id}>
              {s.tracking_number}
            </option>
          ))}
        </select>
        <input
          required
          placeholder="Description"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          className="col-span-2 rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        />
        <input
          required
          type="number"
          step="0.01"
          min="0"
          placeholder="Weight (kg)"
          value={form.weight_kg}
          onChange={(e) => setForm({ ...form, weight_kg: e.target.value })}
          className="rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        />
        <input
          required
          type="number"
          step="0.01"
          min="0"
          placeholder="Declared value"
          value={form.declared_value}
          onChange={(e) => setForm({ ...form, declared_value: e.target.value })}
          className="rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        />
        {error && <p className="col-span-2 font-typewriter text-xs text-saul-rust">{error}</p>}
        <div className="col-span-2 flex gap-2">
          <button
            type="submit"
            disabled={isSaving}
            className="rounded-sm bg-saul-teal px-4 py-2 font-display text-lg tracking-wide text-saul-cream disabled:opacity-40"
          >
            {isSaving ? 'Saving…' : editingId ? 'Save changes' : 'Create package'}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={cancelEdit}
              className="rounded-sm border border-saul-black/30 px-4 py-2 font-display text-lg tracking-wide text-saul-black"
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {isLoading ? (
        <p className="font-typewriter text-sm text-saul-black/60">Loading…</p>
      ) : (
        <AdminTable columns={columns} rows={packages} onEdit={startEdit} onDelete={handleDelete} />
      )}
    </div>
  );
}

export default PackageManager;
