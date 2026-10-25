import type { AdminConversation } from '../../lib/adminApi'
import DataTable from './DataTable'
import type { Column } from './DataTable'
import StatusBadge from './StatusBadge'

type ConversationsTabProps = {
  conversations: AdminConversation[]
}

export default function ConversationsTab({ conversations }: ConversationsTabProps) {
  const columns: Column<AdminConversation>[] = [
    { key: 'conversation_id', label: 'Conversation', sortable: true },
    { key: 'date', label: 'Date', sortable: true },
    { key: 'time', label: 'Time' },
    { key: 'patient_name', label: 'Patient', sortable: true },
    {
      key: 'phone_masked',
      label: 'Phone',
      render: (row) => (
        <span title="Full number is hidden for privacy">{row.phone_masked || '-'}</span>
      ),
    },
    { key: 'topics', label: 'Topics' },
    {
      key: 'booking_status',
      label: 'Booking',
      sortable: true,
      render: (row) => (row.booking_status ? <StatusBadge status={row.booking_status} /> : '-'),
    },
    { key: 'doctor', label: 'Doctor' },
    {
      key: 'summary',
      label: 'Summary',
      render: (row) => <span className="line-clamp-2 max-w-xs text-primary/80">{row.summary}</span>,
    },
  ]

  return (
    <DataTable
      columns={columns}
      rows={conversations}
      rowKey={(row) => row.conversation_id ?? `${row.date}-${row.time}`}
      searchKeys={['conversation_id', 'patient_name', 'doctor', 'topics', 'summary']}
      searchPlaceholder="Search by patient, doctor, topic..."
      statusKey="booking_status"
      statusOptions={['Booked', 'Not booked']}
      emptyMessage="No conversations saved yet."
    />
  )
}
