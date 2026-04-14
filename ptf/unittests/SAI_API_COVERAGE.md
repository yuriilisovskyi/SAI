# SAI API Test Coverage

Generated from `sai_api_attributes.json` and the test files in `ptf/unittests/`.

## Summary

| Metric | Count | % of total |
|---|---|---|
| **Total Thrift functions** | 556 | 100% |
| **Covered** | 502 | **90%** |
| Skipped – bulk ops | 26 | 5% |
| Skipped – entry-type (no key struct) | 28 | 5% |
| Skipped – other / custom args | 0 | 0% |

## Skip reasons

| Reason | Description |
|---|---|
| **Bulk** | `sai_thrift_bulk_create/remove/get/set_*` functions require a caller-supplied list of entry structs and attribute arrays. The test engine cannot construct these from default values alone. |
| **Entry** | Entry-type objects (`INSEG_ENTRY`, `IPMC_ENTRY`, `L2MC_ENTRY`, `MCAST_FDB_ENTRY`, `MY_SID_ENTRY`, `NAT_ENTRY`, `PREFIX_COMPRESSION_ENTRY`) require a pre-built key struct (e.g. `sai_thrift_inseg_entry_t`) containing network-specific fields that have no JSON defaults. `FDB_ENTRY`, `NEIGHBOR_ENTRY`, and `ROUTE_ENTRY` are covered at 55–100% via their specialized test files. |

## Per-object coverage

| SAI Object Type | Total | Covered | Bulk-skip | Entry-skip |
|---|---|---|---|---|
| SAI_OBJECT_TYPE_ACL_COUNTER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ACL_ENTRY | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ACL_RANGE | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ACL_TABLE | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ACL_TABLE_CHAIN_GROUP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ACL_TABLE_GROUP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ACL_TABLE_GROUP_MEMBER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ARS | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ARS_PROFILE | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_BFD_SESSION | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_BRIDGE | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_BRIDGE_PORT | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_BUFFER_POOL | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_BUFFER_PROFILE | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_COUNTER | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_DEBUG_COUNTER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_DTEL | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_DTEL_EVENT | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_DTEL_INT_SESSION | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_DTEL_QUEUE_REPORT | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_DTEL_REPORT_SESSION | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_FDB_ENTRY | 9 | 5 (55%) | 4 | 0 |
| SAI_OBJECT_TYPE_FINE_GRAINED_HASH_FIELD | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_GENERIC_PROGRAMMABLE | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_HASH | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_HOSTIF | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_HOSTIF_PACKET | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_HOSTIF_TABLE_ENTRY | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_HOSTIF_TRAP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_HOSTIF_TRAP_GROUP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_HOSTIF_USER_DEFINED_TRAP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ICMP_ECHO_SESSION | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_INGRESS_PRIORITY_GROUP | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_INSEG_ENTRY | 8 | 0 (0%) | 4 | 4 |
| SAI_OBJECT_TYPE_IPMC_ENTRY | 4 | 0 (0%) | 0 | 4 |
| SAI_OBJECT_TYPE_IPMC_GROUP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_IPMC_GROUP_MEMBER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_IPSEC | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_IPSEC_PORT | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_IPSEC_SA | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ISOLATION_GROUP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ISOLATION_GROUP_MEMBER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_L2MC_ENTRY | 4 | 0 (0%) | 0 | 4 |
| SAI_OBJECT_TYPE_L2MC_GROUP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_L2MC_GROUP_MEMBER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_LAG | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_LAG_MEMBER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_MACSEC | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_MACSEC_FLOW | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_MACSEC_PORT | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_MACSEC_SA | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_MACSEC_SC | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_MCAST_FDB_ENTRY | 4 | 0 (0%) | 0 | 4 |
| SAI_OBJECT_TYPE_MIRROR_SESSION | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_MY_MAC | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_MY_SID_ENTRY | 8 | 0 (0%) | 4 | 4 |
| SAI_OBJECT_TYPE_NAT_ENTRY | 8 | 0 (0%) | 4 | 4 |
| SAI_OBJECT_TYPE_NAT_ZONE_COUNTER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_NEIGHBOR_ENTRY | 9 | 5 (55%) | 4 | 0 |
| SAI_OBJECT_TYPE_NEXT_HOP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_NEXT_HOP_GROUP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MAP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_NEXT_HOP_GROUP_MEMBER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_POE_DEVICE | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_POE_PORT | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_POE_PSE | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_POLICER | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_PORT | 8 | 8 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_PORT_CONNECTOR | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_PORT_POOL | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_PORT_SERDES | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_PREFIX_COMPRESSION_ENTRY | 6 | 0 (0%) | 2 | 4 |
| SAI_OBJECT_TYPE_PREFIX_COMPRESSION_TABLE | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_QOS_MAP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_QUEUE | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ROUTER_INTERFACE | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_ROUTE_ENTRY | 8 | 4 (50%) | 4 | 0 |
| SAI_OBJECT_TYPE_RPF_GROUP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_RPF_GROUP_MEMBER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_SAMPLEPACKET | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_SCHEDULER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_SCHEDULER_GROUP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_SRV6_SIDLIST | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_STP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_STP_PORT | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_SWITCH | 13 | 13 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_SWITCH_TUNNEL | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_SYNCE_CLOCK | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_SYSTEM_PORT | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TAM | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TAM_COLLECTOR | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TAM_COUNTER_SUBSCRIPTION | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TAM_EVENT | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TAM_EVENT_ACTION | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TAM_EVENT_THRESHOLD | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TAM_INT | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TAM_MATH_FUNC | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TAM_REPORT | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TAM_TELEMETRY | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TAM_TEL_TYPE | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TAM_TRANSPORT | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TUNNEL | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TUNNEL_MAP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TUNNEL_MAP_ENTRY | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TUNNEL_TERM_TABLE_ENTRY | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_TWAMP_SESSION | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_UDF | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_UDF_GROUP | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_UDF_MATCH | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_VIRTUAL_ROUTER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_VLAN | 7 | 7 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_VLAN_MEMBER | 4 | 4 (100%) | 0 | 0 |
| SAI_OBJECT_TYPE_WRED | 4 | 4 (100%) | 0 | 0 |
| **TOTAL** | **556** | **502 (90%)** | **26** | **28** |

## Entry-type objects not covered (28 functions)

These objects require a pre-built network-specific key struct that cannot be derived
from JSON default values. Specialized tests would need to construct the entry key
from live network state (e.g. interface IDs, label values, IP addresses from the
control plane).

| Object Type | Skipped functions | Reason |
|---|---|---|
| SAI_OBJECT_TYPE_INSEG_ENTRY | create, get, set, remove + 4 bulk | MPLS In-Segment entry requires `label` (MPLS label stack value) |
| SAI_OBJECT_TYPE_IPMC_ENTRY | create, get, set, remove | IP multicast entry requires `vr_id`, `type`, `destination`, `source` |
| SAI_OBJECT_TYPE_L2MC_ENTRY | create, get, set, remove | L2 multicast entry requires `bv_id`, `type`, `destination`, `source` |
| SAI_OBJECT_TYPE_MCAST_FDB_ENTRY | create, get, set, remove | Multicast FDB entry requires `mac_address` + `bv_id` with multicast group |
| SAI_OBJECT_TYPE_MY_SID_ENTRY | create, get, set, remove + 4 bulk | SRv6 My SID entry requires IPv6 SID address |
| SAI_OBJECT_TYPE_NAT_ENTRY | create, get, set, remove + 4 bulk | NAT entry requires `vr_id` + NAT data (IP/port translation tuple) |
| SAI_OBJECT_TYPE_PREFIX_COMPRESSION_ENTRY | create, get, set, remove + 2 bulk | Requires `table_id` OID from a prefix compression table |

## Bulk functions not covered (26 functions)

All `sai_thrift_bulk_*` variants are skipped because they require the caller to
supply a list of pre-built entry structs and matching attribute arrays. The test
engine derives arguments from scalar JSON defaults and cannot construct these lists.

Affected objects: FDB_ENTRY (4), NEIGHBOR_ENTRY (4), ROUTE_ENTRY (4),
INSEG_ENTRY (4), MY_SID_ENTRY (4), NAT_ENTRY (4), PREFIX_COMPRESSION_ENTRY (2).
