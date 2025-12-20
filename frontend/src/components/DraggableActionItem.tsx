import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Trash2, Clock, User } from 'lucide-react';
import { ActionItem } from '../services/api';

interface Props {
  id: string;
  item: ActionItem;
  index: number;
  onUpdate: (index: number, field: keyof ActionItem, value: string) => void;
  onRemove: (index: number) => void;
}

const statusColors = {
  'Pending': 'bg-yellow-50 border-yellow-200 text-yellow-800',
  'In Progress': 'bg-blue-50 border-blue-200 text-blue-800',
  'Completed': 'bg-green-50 border-green-200 text-green-800',
  'Blocked': 'bg-red-50 border-red-200 text-red-800',
};

export default function DraggableActionItem({ id, item, index, onUpdate, onRemove }: Props) {
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
      className="flex gap-3 items-start p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
    >
      <button
        {...attributes}
        {...listeners}
        className="mt-2 text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing"
      >
        <GripVertical className="h-5 w-5" />
      </button>
      <div className="flex-1 space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
          <textarea
            value={item.description}
            onChange={(e) => onUpdate(index, 'description', e.target.value)}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="What needs to be done?"
          />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
              <User className="h-3 w-3" />
              Owner
            </label>
            <input
              type="text"
              value={item.owner}
              onChange={(e) => onUpdate(index, 'owner', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="Responsible person"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Due Date
            </label>
            <input
              type="date"
              value={item.due_date || ''}
              onChange={(e) => onUpdate(index, 'due_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
            <select
              value={item.status}
              onChange={(e) => onUpdate(index, 'status', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
                statusColors[item.status as keyof typeof statusColors] || 'bg-white'
              }`}
            >
              <option value="Pending">Pending</option>
              <option value="In Progress">In Progress</option>
              <option value="Completed">Completed</option>
              <option value="Blocked">Blocked</option>
            </select>
          </div>
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
