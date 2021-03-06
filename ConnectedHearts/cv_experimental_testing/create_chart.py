import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

sns.set(style="darkgrid")

results = pd.read_csv("experiment_synch_data.csv")
print results.head()

results.set_index('time').plot()

plt.ylim([-0.5,1.5])
plt.show()

