import pandas as pd
import matplotlib.pyplot as plt

files = {
    "results_deviation_latency_localhost": "client/results/results_deviation_latency_localhost.csv",
    "results_feature_latency_localhost": "client/results/results_feature_latency_localhost.csv",
    "results_latency_deviation_lan": "client/results/results_latency_deviation_lan.csv",
    "results_latency_feature_lan": "client/results/results_latency_feature_lan.csv",
    "results_DeviationClassifier_lan": "server/results/results_DeviationClassifier_lan.csv",
    "results_DeviationClassifier_localhost": "server/results/results_DeviationClassifier_localhost.csv",
    "results_FeatureClassifier_lan": "server/results/results_FeatureClassifier_lan.csv",
    "results_FeatureClassifier_localhost": "server/results/results_FeatureClassifier_localhost.csv",
}

dataframes = {name: pd.read_csv(path) for name, path in files.items()}

for name, df in dataframes.items():
    if 'duration_ms' in df.columns:
        df.rename(columns={'duration_ms': 'duration'}, inplace=True)
    else:
        df['duration'] = df['duration'] - 1000

latency_deviation_localhost = dataframes['results_deviation_latency_localhost']
latency_feature_localhost = dataframes['results_feature_latency_localhost']
latency_deviation_lan = dataframes['results_latency_deviation_lan']
latency_feature_lan = dataframes['results_latency_feature_lan']

processing_deviation_localhost = dataframes['results_DeviationClassifier_localhost']
processing_feature_localhost = dataframes['results_FeatureClassifier_localhost']
processing_deviation_lan = dataframes['results_DeviationClassifier_lan']
processing_feature_lan = dataframes['results_FeatureClassifier_lan']

# Calculate mean and standard deviation
stats = {}


def calculate_stats(df, label):
    mean = df['duration'].mean()
    std = df['duration'].std()
    med = df['duration'].median()
    stats[label] = {"mean": mean, "std": std, "med": med}


# Latency stats
calculate_stats(latency_deviation_localhost, 'latency_deviation_localhost')
calculate_stats(latency_feature_localhost, 'latency_feature_localhost')
calculate_stats(latency_deviation_lan, 'latency_deviation_lan')
calculate_stats(latency_feature_lan, 'latency_feature_lan')

# Processing time stats
calculate_stats(processing_deviation_localhost, 'processing_deviation_localhost')
calculate_stats(processing_feature_localhost, 'processing_feature_localhost')
calculate_stats(processing_deviation_lan, 'processing_deviation_lan')
calculate_stats(processing_feature_lan, 'processing_feature_lan')

# Plot histograms
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Latency - Localhost
axes[0, 0].hist(latency_deviation_localhost['duration'], bins=30, alpha=0.5, label='Deviation Classifier')
axes[0, 0].hist(latency_feature_localhost['duration'], bins=30, alpha=0.5, label='Feature Classifier')
axes[0, 0].set_title('Latency on Localhost')
axes[0, 0].set_xlabel('Milliseconds')
axes[0, 0].set_ylabel('Messages')
axes[0, 0].legend()

# Latency - LAN
axes[0, 1].hist(latency_deviation_lan['duration'], bins=30, alpha=0.5, label='Deviation Classifier')
axes[0, 1].hist(latency_feature_lan['duration'], bins=30, alpha=0.5, label='Feature Classifier')
axes[0, 1].set_title('Latency on LAN')
axes[0, 1].set_xlabel('Milliseconds')
axes[0, 1].set_ylabel('Messages')
axes[0, 1].legend()

# Processing Time - Localhost
axes[1, 0].hist(processing_deviation_localhost['duration'], bins=30, alpha=0.5, label='Deviation Classifier')
axes[1, 0].hist(processing_feature_localhost['duration'], bins=30, alpha=0.5, label='Feature Classifier')
axes[1, 0].set_title('Processing Time on Localhost')
axes[1, 0].set_xlabel('Milliseconds')
axes[1, 0].set_ylabel('Messages')
axes[1, 0].legend()

# Processing Time - LAN
axes[1, 1].hist(processing_deviation_lan['duration'], bins=30, alpha=0.5, label='Deviation Classifier')
axes[1, 1].hist(processing_feature_lan['duration'], bins=30, alpha=0.5, label='Feature Classifier')
axes[1, 1].set_title('Processing Time on LAN')
axes[1, 1].set_xlabel('Milliseconds')
axes[1, 1].set_ylabel('Messages')
axes[1, 1].legend()

print(stats)
plt.tight_layout()
plt.savefig("classifier_histograms.png")
plt.show()
