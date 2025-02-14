#!/usr/bin/python3
import matplotlib.pyplot as plt
import seaborn as sns

data = []

plt.figure(figsize=(8, 5))
sns.histplot(data, bins=100, kde=True)
plt.show()
