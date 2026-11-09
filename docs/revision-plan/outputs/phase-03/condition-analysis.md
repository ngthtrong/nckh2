# Phân tích từng điều kiện

Primary và replication tách riêng; không tăng n bằng scenario/copy.

## RQ1 primary

| Scenario | Method | ARI mean | density | false destination % |
|---|---|---:|---:|---:|
| baseline | additive_cij_louvain | 0.91906 | 0.02896 | 15.8444 |
| baseline | additive_cij_louvain_matched_density | 0.89733 | 0.03021 | 16.3814 |
| baseline | geo_time_dbscan | 0.49781 | nan | 23.9348 |
| baseline | product_cij_leiden | 0.91649 | 0.03011 | 16.4099 |
| baseline | product_cij_louvain | 0.90722 | 0.03011 | 16.4907 |
| exact_transport_copy_2x | additive_cij_louvain | 0.93368 | 0.01560 | 16.2536 |
| exact_transport_copy_2x | additive_cij_louvain_matched_density | 0.91810 | 0.01572 | 16.8864 |
| exact_transport_copy_2x | geo_time_dbscan | 0.49781 | nan | 23.9348 |
| exact_transport_copy_2x | product_cij_leiden | 0.93127 | 0.01574 | 16.9135 |
| exact_transport_copy_2x | product_cij_louvain | 0.93139 | 0.01574 | 16.9317 |
| exact_transport_copy_5x | additive_cij_louvain | 0.29710 | 0.00615 | 18.3411 |
| exact_transport_copy_5x | additive_cij_louvain_matched_density | 0.29167 | 0.00615 | 18.4433 |
| exact_transport_copy_5x | geo_time_dbscan | 0.49781 | nan | 23.9348 |
| exact_transport_copy_5x | product_cij_leiden | 0.29642 | 0.00616 | 18.4677 |
| exact_transport_copy_5x | product_cij_louvain | 0.29642 | 0.00616 | 18.4677 |
| gps_noise_100m | additive_cij_louvain | 0.89706 | 0.02915 | 16.1248 |
| gps_noise_100m | additive_cij_louvain_matched_density | 0.87871 | 0.03033 | 16.6156 |
| gps_noise_100m | geo_time_dbscan | 0.46779 | nan | 24.9683 |
| gps_noise_100m | product_cij_leiden | 0.90471 | 0.03035 | 16.2229 |
| gps_noise_100m | product_cij_louvain | 0.89563 | 0.03035 | 16.2817 |
| gps_noise_300m | additive_cij_louvain | 0.76257 | 0.02912 | 17.8614 |
| gps_noise_300m | additive_cij_louvain_matched_density | 0.79908 | 0.03096 | 18.1924 |
| gps_noise_300m | geo_time_dbscan | 0.37090 | nan | 27.6973 |
| gps_noise_300m | product_cij_leiden | 0.79118 | 0.03074 | 18.1707 |
| gps_noise_300m | product_cij_louvain | 0.78162 | 0.03074 | 18.2181 |
| time_noise_15min | additive_cij_louvain | 0.88151 | 0.02902 | 16.6787 |
| time_noise_15min | additive_cij_louvain_matched_density | 0.85359 | 0.03031 | 17.2682 |
| time_noise_15min | geo_time_dbscan | 0.48561 | nan | 24.7063 |
| time_noise_15min | product_cij_leiden | 0.88501 | 0.03018 | 17.0122 |
| time_noise_15min | product_cij_louvain | 0.87224 | 0.03018 | 17.0256 |
| time_noise_60min | additive_cij_louvain | 0.76458 | 0.02848 | 18.4038 |
| time_noise_60min | additive_cij_louvain_matched_density | 0.70746 | 0.03033 | 20.2952 |
| time_noise_60min | geo_time_dbscan | 0.44320 | nan | 25.0494 |
| time_noise_60min | product_cij_leiden | 0.76043 | 0.02992 | 19.0293 |
| time_noise_60min | product_cij_louvain | 0.74420 | 0.02992 | 19.3267 |
## RQ1 replication

| Scenario | Method | ARI mean | density | false destination % |
|---|---|---:|---:|---:|
| baseline | additive_cij_louvain | 0.91906 | 0.02896 | 15.8444 |
| baseline | additive_cij_louvain_matched_density | 0.89733 | 0.03021 | 16.3814 |
| baseline | geo_time_dbscan | 0.49781 | nan | 23.9348 |
| baseline | product_cij_leiden | 0.91649 | 0.03011 | 16.4099 |
| baseline | product_cij_louvain | 0.90722 | 0.03011 | 16.4907 |
| exact_transport_copy_2x | additive_cij_louvain | 0.93218 | 0.01561 | 16.4726 |
| exact_transport_copy_2x | additive_cij_louvain_matched_density | 0.91827 | 0.01571 | 16.8027 |
| exact_transport_copy_2x | geo_time_dbscan | 0.49781 | nan | 23.9348 |
| exact_transport_copy_2x | product_cij_leiden | 0.92891 | 0.01574 | 16.9254 |
| exact_transport_copy_2x | product_cij_louvain | 0.93416 | 0.01574 | 16.9557 |
| exact_transport_copy_5x | additive_cij_louvain | 0.29710 | 0.00615 | 18.3411 |
| exact_transport_copy_5x | additive_cij_louvain_matched_density | 0.29167 | 0.00615 | 18.4433 |
| exact_transport_copy_5x | geo_time_dbscan | 0.49781 | nan | 23.9348 |
| exact_transport_copy_5x | product_cij_leiden | 0.29642 | 0.00616 | 18.4677 |
| exact_transport_copy_5x | product_cij_louvain | 0.29642 | 0.00616 | 18.4677 |
| gps_noise_100m | additive_cij_louvain | 0.89706 | 0.02915 | 16.1248 |
| gps_noise_100m | additive_cij_louvain_matched_density | 0.87871 | 0.03033 | 16.6156 |
| gps_noise_100m | geo_time_dbscan | 0.46779 | nan | 24.9683 |
| gps_noise_100m | product_cij_leiden | 0.90471 | 0.03035 | 16.2229 |
| gps_noise_100m | product_cij_louvain | 0.89563 | 0.03035 | 16.2817 |
| gps_noise_300m | additive_cij_louvain | 0.76257 | 0.02912 | 17.8614 |
| gps_noise_300m | additive_cij_louvain_matched_density | 0.79908 | 0.03096 | 18.1924 |
| gps_noise_300m | geo_time_dbscan | 0.37090 | nan | 27.6973 |
| gps_noise_300m | product_cij_leiden | 0.79118 | 0.03074 | 18.1707 |
| gps_noise_300m | product_cij_louvain | 0.78162 | 0.03074 | 18.2181 |
| time_noise_15min | additive_cij_louvain | 0.88151 | 0.02902 | 16.6787 |
| time_noise_15min | additive_cij_louvain_matched_density | 0.85359 | 0.03031 | 17.2682 |
| time_noise_15min | geo_time_dbscan | 0.48561 | nan | 24.7063 |
| time_noise_15min | product_cij_leiden | 0.88501 | 0.03018 | 17.0122 |
| time_noise_15min | product_cij_louvain | 0.87224 | 0.03018 | 17.0256 |
| time_noise_60min | additive_cij_louvain | 0.76458 | 0.02848 | 18.4038 |
| time_noise_60min | additive_cij_louvain_matched_density | 0.70746 | 0.03033 | 20.2952 |
| time_noise_60min | geo_time_dbscan | 0.44320 | nan | 25.0494 |
| time_noise_60min | product_cij_leiden | 0.76043 | 0.02992 | 19.0293 |
| time_noise_60min | product_cij_louvain | 0.74420 | 0.02992 | 19.3267 |

## RQ2 sensitivity

- b0: min/max mean NDCG 0.66534127/0.66720560; nguồn rq2_parameter_sensitivity_summary.csv, không retune.
- b1: min/max mean NDCG 0.66688974/0.66874356; nguồn rq2_parameter_sensitivity_summary.csv, không retune.
- b2: min/max mean NDCG 0.66669134/0.66793359; nguồn rq2_parameter_sensitivity_summary.csv, không retune.
- mu: min/max mean NDCG 0.66441533/0.66832420; nguồn rq2_parameter_sensitivity_summary.csv, không retune.
- n_ref: min/max mean NDCG 0.66685740/0.66688974; nguồn rq2_parameter_sensitivity_summary.csv, không retune.
- omega_e: min/max mean NDCG 0.66634334/0.67141623; nguồn rq2_parameter_sensitivity_summary.csv, không retune.
- omega_f: min/max mean NDCG 0.66246690/0.66792686; nguồn rq2_parameter_sensitivity_summary.csv, không retune.
- omega_n: min/max mean NDCG 0.66631779/0.66970089; nguồn rq2_parameter_sensitivity_summary.csv, không retune.
- s: min/max mean NDCG 0.66654560/0.67134023; nguồn rq2_parameter_sensitivity_summary.csv, không retune.
- v_cap: min/max mean NDCG 0.66688974/0.66688974; nguồn rq2_parameter_sensitivity_summary.csv, không retune.

## RQ3 resource conditions: mô tả, không n120

```text
                                     latent_harm  deadline_miss_rate
resource_scenario  policy                                           
lean_hue           legacy_priority    653.793367            0.920312
                   nearest_first      585.551188            0.820312
                   revised_priority   691.370208            0.918750
nominal_dual_depot legacy_priority    303.161859            0.859375
                   nearest_first      229.999202            0.631250
                   revised_priority   315.013181            0.845313
regional_surge     legacy_priority    119.932580            0.707812
                   nearest_first       94.707932            0.448437
                   revised_priority   113.528851            0.667188
```
