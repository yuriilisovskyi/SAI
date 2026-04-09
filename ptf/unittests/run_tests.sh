#!/bin/bash
# Auto-generated list of PTF test commands for all SAI API unit tests.
# Each line runs one per-header test class against a live SAI device.
#
# Usage:
#   cd <repo-root>
#   bash ptf/unittests/run_tests.sh
#
# Or execute individual lines directly.

./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiacl_test.SaiAclTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiars_test.SaiArsTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiarsprofile_test.SaiArsprofileTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saibfd_test.SaiBfdTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saibridge_test.SaiBridgeTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saibuffer_test.SaiBufferTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saicounter_test.SaiCounterTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saidebugcounter_test.SaiDebugcounterTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saidtel_test.SaiDtelTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saifdb_test.SaiFdbTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saigenericprogrammable_test.SaiGenericprogrammableTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saihash_test.SaiHashTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saihostif_test.SaiHostifTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiicmpecho_test.SaiIcmpechoTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiipmc_test.SaiIpmcTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiipmcgroup_test.SaiIpmcgroupTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiipsec_test.SaiIpsecTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiisolationgroup_test.SaiIsolationgroupTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" sail2mc_test.SaiL2mcTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" sail2mcgroup_test.SaiL2mcgroupTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" sailag_test.SaiLagTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saimacsec_test.SaiMacsecTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saimcastfdb_test.SaiMcastfdbTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saimirror_test.SaiMirrorTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saimpls_test.SaiMplsTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saimymac_test.SaiMymacTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" sainat_test.SaiNatTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saineighbor_test.SaiNeighborTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" sainexthop_test.SaiNexthopTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" sainexthopgroup_test.SaiNexthopgroupTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saipoe_test.SaiPoeTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saipolicer_test.SaiPolicerTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiport_test.SaiPortTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiprefixcompression_test.SaiPrefixcompressionTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiqosmap_test.SaiQosmapTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiqueue_test.SaiQueueTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" sairoute_test.SaiRouteTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" sairouterinterface_test.SaiRouterinterfaceTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" sairpfgroup_test.SaiRpfgroupTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saisamplepacket_test.SaiSamplepacketTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saischeduler_test.SaiSchedulerTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saischedulergroup_test.SaiSchedulergroupTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saisrv6_test.SaiSrv6Test
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saistp_test.SaiStpTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiswitch_test.SaiSwitchTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saisynce_test.SaiSynceTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saisystemport_test.SaiSystemportTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saitam_test.SaiTamTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saitunnel_test.SaiTunnelTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saitwamp_test.SaiTwampTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiudf_test.SaiUdfTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saivirtualrouter_test.SaiVirtualrouterTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saivlan_test.SaiVlanTest
./SAI/test/ptf/ptf --test-dir SAI/ptf/unittests --test-params="port_map_file='config/ptf_port_map.ini'" saiwred_test.SaiWredTest
