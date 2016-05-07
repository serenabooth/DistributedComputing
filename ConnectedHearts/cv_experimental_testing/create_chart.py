import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

sns.set(style="darkgrid")

results = pd.read_csv("experiment_synch_data.csv")
#results = results.set_index(results.time)


print results.head()

colors = sns.cubehelix_palette(8, start=0, rot=-.75)

results.set_index('time').plot()
plt.show()

