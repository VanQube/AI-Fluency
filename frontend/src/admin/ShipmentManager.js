import { useState } from 'react';
import {
  useListShipments,
  useCreateShipment,
  useUpdateShipment,
  useDeleteShipment,
  useListCustomers,
} from '../api/generated/secureship';
import AdminTable from './AdminTable';
import { authFetch } from './authFetch';

// Matches backend/models/shipment.py's SHIPMENT_STATUSES — kept in sync by
// hand since the enum isn't exposed as its own endpoint.
const STATUSES = ['label_created', 'in_transit', 'out_for_delivery', 'delivered', 'exception'];

const EMPTY_FORM = {
  customer_id: '',
  tracking_number: '',
  status: STATUSES[0],
  carrier: '',
  origin: '',
  destination: '',
  estimated_delivery: '',
  last_update: '',
};

function toDatetimeLocal(isoString) {
  return isoString ? isoString.slice(0, 16) : '';
}

function ShipmentManager({ token }) {
  const { data, refetch, isLoading } = useListShipments({ fetch: authFetch(token) });
  const { data: customersData } = useListCustomers({ fetch: authFetch(token) });
  const createShipment = useCreateShipment({ fetch: authFetch(token) });
  const updateShipment = useUpdateShipment({ fetch: authFetch(token) });
  const deleteShipment = useDeleteShipment({ fetch: authFetch(token) });

  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);

  const shipments = data?.data ?? [];
  const customers = customersData?.data ?? [];
  const customerName = (id) => {
    const c = customers.find((customer) => customer.id === id);
    return c ? `${c.first_name} ${c.last_name}` : id;
  };

  const columns = [
    { key: 'tracking_number', label: 'Tracking #' },
    { key: 'customer_id', label: 'Customer', render: (row) => customerName(row.customer_id) },
    { key: 'status', label: 'Status' },
    { key: 'carrier', label: 'Carrier' },
    { key: 'destination', label: 'Destination' },
  ];

  function startEdit(shipment) {
    setEditingId(shipment.id);
    setForm({
      customer_id: shipment.customer_id,
      tracking_number: shipment.tracking_number,
      status: shipment.status,
      carrier: shipment.carrier,
      origin: shipment.origin,
      destination: shipment.destination,
      estimated_delivery: shipment.estimated_delivery,
      last_update: toDatetimeLocal(shipment.last_update),
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

    if (!form.customer_id) {
      setError('Pick a customer.');
      return;
    }

    const payload = { ...form, last_update: new Date(form.last_update).toISOString() };
    const result = editingId
      ? await updateShipment.mutateAsync({ shipmentId: editingId, data: payload })
      : await createShipment.mutateAsync({ data: payload });

    if (result.status !== 200 && result.status !== 201) {
      setError('Save failed — check the fields and try again.');
      return;
    }
    await refetch();
    cancelEdit();
  }

  async function handleDelete(shipment) {
    setError(null);
    const result = await deleteShipment.mutateAsync({ shipmentId: shipment.id });
    if (result.status !== 204) {
      setError(
        result.status === 409
          ? 'Could not delete — this shipment still has packages on file.'
          : 'Could not delete — try again.'
      );
      return;
    }
    await refetch();
  }

  const isSaving = createShipment.isPending || updateShipment.isPending;

  return (
    <div>
      <form
        onSubmit={handleSubmit}
        className="mb-6 grid grid-cols-2 gap-3 rounded-sm border border-saul-black/20 bg-white p-4"
      >
        <h3 className="col-span-2 font-display text-xl tracking-wide text-saul-black">
          {editingId ? 'Edit shipment' : 'New shipment'}
        </h3>
        <select
          required
          value={form.customer_id}
          onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
          className="rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        >
          <option value="">Select customer…</option>
          {customers.map((c) => (
            <option key={c.id} value={c.id}>
              {c.first_name} {c.last_name}
            </option>
          ))}
        </select>
        <select
          value={form.status}
          onChange={(e) => setForm({ ...form, status: e.target.value })}
          className="rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <input
          required
          placeholder="Tracking number"
          value={form.tracking_number}
          onChange={(e) => setForm({ ...form, tracking_number: e.target.value })}
          className="rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        />
        <input
          required
          placeholder="Carrier"
          value={form.carrier}
          onChange={(e) => setForm({ ...form, carrier: e.target.value })}
          className="rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        />
        <input
          required
          placeholder="Origin"
          value={form.origin}
          onChange={(e) => setForm({ ...form, origin: e.target.value })}
          className="rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        />
        <input
          required
          placeholder="Destination"
          value={form.destination}
          onChange={(e) => setForm({ ...form, destination: e.target.value })}
          className="rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        />
        <label className="flex flex-col font-typewriter text-xs text-saul-black/70">
          Estimated delivery
          <input
            required
            type="date"
            value={form.estimated_delivery}
            onChange={(e) => setForm({ ...form, estimated_delivery: e.target.value })}
            className="mt-1 rounded-sm border border-saul-black/30 px-3 py-2 text-sm"
          />
        </label>
        <label className="flex flex-col font-typewriter text-xs text-saul-black/70">
          Last update
          <input
            required
            type="datetime-local"
            value={form.last_update}
            onChange={(e) => setForm({ ...form, last_update: e.target.value })}
            className="mt-1 rounded-sm border border-saul-black/30 px-3 py-2 text-sm"
          />
        </label>
        {error && <p className="col-span-2 font-typewriter text-xs text-saul-rust">{error}</p>}
        <div className="col-span-2 flex gap-2">
          <button
            type="submit"
            disabled={isSaving}
            className="rounded-sm bg-saul-teal px-4 py-2 font-display text-lg tracking-wide text-saul-cream disabled:opacity-40"
          >
            {isSaving ? 'Saving…' : editingId ? 'Save changes' : 'Create shipment'}
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
        <AdminTable columns={columns} rows={shipments} onEdit={startEdit} onDelete={handleDelete} />
      )}
    </div>
  );
}

export default ShipmentManager;
