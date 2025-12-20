import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Trash2, UserCheck, UserX } from 'lucide-react';
import { Attendee } from '../services/api';

interface Props {
  id: string;
  attendee: Attendee;
  index: number;
  onUpdate: (index: number, field: keyof Attendee, value: string | boolean) => void;
  onRemove: (index: number) => void;
}

export default function DraggableAttendee({ id, attendee, index, onUpdate, onRemove }: Props) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex gap-3 items-center p-3 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
    >
      <button
        {...attributes}
        {...listeners}
        className="text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing"
      >
        <GripVertical className="h-5 w-5" />
      </button>
      <div className="flex-1">
        <input
          type="text"
          value={attendee.name}
          onChange={(e) => onUpdate(index, 'name', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          placeholder="Name"
        />
      </div>
      <button
        onClick={() => onUpdate(index, 'attended', !attendee.attended)}
        className={`flex items-center gap-2 px-3 py-2 rounded-md border transition-colors ${
          attendee.attended
            ? 'bg-green-50 border-green-200 text-green-700 hover:bg-green-100'
            : 'bg-gray-50 border-gray-200 text-gray-500 hover:bg-gray-100'
        }`}
      >
        {attendee.attended ? (
          <>
            <UserCheck className="h-4 w-4" />
            <span className="text-sm font-medium">Attended</span>
          </>
        ) : (
          <>
            <UserX className="h-4 w-4" />
            <span className="text-sm font-medium">Absent</span>
          </>
        )}
      </button>
      <button
        onClick={() => onRemove(index)}
        className="text-red-500 hover:text-red-700 p-1 hover:bg-red-50 rounded"
      >
        <Trash2 className="h-5 w-5" />
      </button>
    </div>
  );
}
