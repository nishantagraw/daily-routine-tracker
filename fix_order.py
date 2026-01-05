import json

# Load data
with open('tracker_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Define proper order
proper_order = [
    'Calisthenics',
    'Water',
    'Running',
    'Sleep',
    'Python',
    'Protein',
    'Client',
    'Reading',
    'Meditation',
    'Social Media',
    'Morning Walk'
]

# Remove DAILY TOTALS and sort properly
habits = [h for h in data['habits'] if 'DAILY TOTALS' not in h.get('name', '')]

# Fix Protein emoji
for h in habits:
    if 'Protein' in h['name'] and not h['name'].startswith('💪'):
        h['name'] = '💪 Protein Intake'
        h['emoji'] = '💪'

# Sort by proper order
def get_order(habit):
    name = habit['name']
    for i, key in enumerate(proper_order):
        if key in name:
            return i
    return 99

habits.sort(key=get_order)

data['habits'] = habits

# Save
with open('tracker_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Fixed order:')
for h in habits:
    name = h['name']
    print(f'  {name}')
