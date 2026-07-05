
from utils import get_cursor_workbench_path, get_resolved_cursor_app_path
from workbench_patches import apply_workbench_patches, count_pending_patches
import shutil
import tempfile
from datetime import datetime

wb_path = get_cursor_workbench_path(get_resolved_cursor_app_path())

# Read current content
with open(wb_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Count pending patches first
pending = count_pending_patches(content)
print('Pending patches before:', pending)

# Apply all patches
patched, applied = apply_workbench_patches(content)
print('Applied patches:', applied)

# Create backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = f"{wb_path}.cfv.{timestamp}.bak"
shutil.copy2(wb_path, backup_path)
print('Saved backup:', backup_path)

# Write patched content
with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", errors="ignore", delete=False) as tmp:
    tmp.write(patched)
    tmp_path = tmp.name
shutil.move(tmp_path, wb_path)
print('Patched workbench written!')

# Verify
with open(wb_path, 'r', encoding='utf-8', errors='ignore') as f:
    head = f.read(1000)
print('CFV-NET-LAG in workbench:', '/*CFV-NET-LAG*/' in head)
