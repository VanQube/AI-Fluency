import { useState } from 'react';
import {
  useListCustomers,
  useCreateCustomer,
  useUpdateCustomer,
  useDeleteCustomer,
} from '../api/generated/secureship';
import AdminTable from './AdminTable';
import { authFetch } from './authFetch';

const EMPTY_FORM = { first_name: '', last_name: '', phone_number: '', address: '' };

const COLUMNS = [
  { key: 'first_name', label: 'First name' },
  { key: 'last_name', label: 'Last name' },
  { key: 'phone_number', label: 'Phone' },
  { key: 'address', label: 'Address' },
];

function CustomerManager({ token }) {
  const { data, refetch, isLoading } = useListCustomers({ fetch: authFetch(token) });
  const createCustomer = useCreateCustomer({ fetch: authFetch(token) });
  const updateCustomer = useUpdateCustomer({ fetch: authFetch(token) });
  const deleteCustomer = useDeleteCustomer({ fetch: authFetch(token) });

  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);

  const customers = data?.data ?? [];

  function startEdit(customer) {
    setEditingId(customer.id);
    setForm({
      first_name: customer.first_name,
      last_name: customer.last_name,
      phone_number: customer.phone_number,
      address: customer.address,
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
    const result = editingId
      ? await updateCustomer.mutateAsync({ customerId: editingId, data: form })
      : await createCustomer.mutateAsync({ data: form });

    if (result.status !== 200 && result.status !== 201) {
      setError('Save failed — check the fields and try again.');
      return;
    }
    await refetch();
    cancelEdit();
  }

  async function handleDelete(customer) {
    setError(null);
    const result = await deleteCustomer.mutateAsync({ customerId: customer.id });
    if (result.status !== 204) {
      setError(
        result.status === 409
          ? 'Could not delete — this customer still has shipments on file.'
          : 'Could not delete — try again.'
      );
      return;
    }
    await refetch();
  }

  const isSaving = createCustomer.isPending || updateCustomer.isPending;

  return (
    <div>
      <form
        onSubmit={handleSubmit}
        className="mb-6 grid grid-cols-2 gap-3 rounded-sm border border-saul-black/20 bg-white p-4"
      >
        <h3 className="col-span-2 font-display text-xl tracking-wide text-saul-black">
          {editingId ? 'Edit customer' : 'New customer'}
        </h3>
        <input
          required
          placeholder="First name"
          value={form.first_name}
          onChange={(e) => setForm({ ...form, first_name: e.target.value })}
          className="rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        />
        <input
          required
          placeholder="Last name"
          value={form.last_name}
          onChange={(e) => setForm({ ...form, last_name: e.target.value })}
          className="rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        />
        <input
          required
          placeholder="Phone number"
          value={form.phone_number}
          onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
          className="rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        />
        <input
          required
          placeholder="Address"
          value={form.address}
          onChange={(e) => setForm({ ...form, address: e.target.value })}
          className="rounded-sm border border-saul-black/30 px-3 py-2 font-typewriter text-sm"
        />
        {error && <p className="col-span-2 font-typewriter text-xs text-saul-rust">{error}</p>}
        <div className="col-span-2 flex gap-2">
          <button
            type="submit"
            disabled={isSaving}
            className="rounded-sm bg-saul-teal px-4 py-2 font-display text-lg tracking-wide text-saul-cream disabled:opacity-40"
          >
            {isSaving ? 'Saving…' : editingId ? 'Save changes' : 'Create customer'}
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
        <AdminTable columns={COLUMNS} rows={customers} onEdit={startEdit} onDelete={handleDelete} />
      )}
    </div>
  );
}

export default CustomerManager;
