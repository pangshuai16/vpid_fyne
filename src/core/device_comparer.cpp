#include "core/device_comparer.h"
#include <set>

namespace vpid {

void DeviceComparer::compare(const std::vector<USBDevice>& oldDev,
                             const std::vector<USBDevice>& newDev,
                             std::vector<USBDevice>& added,
                             std::vector<USBDevice>& removed) {
    std::set<DeviceKey> oldKeys, newKeys;
    for (const auto& d : oldDev) oldKeys.insert(d.getUniqueKey());
    for (const auto& d : newDev) newKeys.insert(d.getUniqueKey());

    added.clear();
    removed.clear();
    for (const auto& d : newDev)
        if (!oldKeys.count(d.getUniqueKey())) added.push_back(d);
    for (const auto& d : oldDev)
        if (!newKeys.count(d.getUniqueKey())) removed.push_back(d);
}

bool DeviceComparer::hasChanged(const std::vector<USBDevice>& a, const std::vector<USBDevice>& b) {
    std::set<DeviceKey> ka, kb;
    for (const auto& d : a) ka.insert(d.getUniqueKey());
    for (const auto& d : b) kb.insert(d.getUniqueKey());
    if (ka.size() != kb.size()) return true;
    for (const auto& k : ka) if (!kb.count(k)) return true;
    return false;
}

} // namespace vpid