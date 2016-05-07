import seaborn as sns
import pandas as pd
sns.set(style="darkgrid")

results = pd.read_csv("experiment_synch_data.csv")

print results.head

colors = sns.cubehelix_palette(8, start=0, rot=-.75)


# Load the long-form example gammas dataset
#gammas = sns.load_dataset("gammas")

# Plot the response with standard error
#sns.tsplot(data=gammas, time="timepoint", unit="subject",
#           condition="ROI", value="BOLD signal")

