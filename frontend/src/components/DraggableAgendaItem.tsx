import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Trash2 } from 'lucide-react';
import { AgendaItem } from '../services/api';

interface Props {
  id: string;
  item: AgendaItem;
  index: number;
  onUpdate: (index: number, field: keyof AgendaItem, value: string) => void;
  onRemove: (index: number) => void;
}

export default function DraggableAgendaItem({ id, item, index, onUpdate, onRemove }: Props) {
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
      className="flex gap-3 items-start p-3 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
    >
      <button
        {...attributes}
        {...listeners}
        className="mt-2 text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing"
      >
        <GripVertical className="h-5 w-5" />
      </button>
      <div className="flex-1 grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Agenda Item</label>
          <input
            type="text"
            value={item.item}
            onChange={(e) => onUpdate(index, 'item', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Review Q4 Performance"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Notes</label>
          <textarea
            value={item.notes}
            onChange={(e) => onUpdate(index, 'notes', e.target.value)}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="Discussion points, outcomes..."
          />
        </div>
      </div>
      <button
        onClick={() => onRemove(index)}
        className="mt-2 text-red-500 hover:text-red-700 p-1 hover:bg-red-50 rounded"
      >
        <Trash2 className="h-5 w-5" />
      </button>
    </div>
  );
}
