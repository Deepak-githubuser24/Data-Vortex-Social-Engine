import os
import json
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

os.makedirs("eda_outputs", exist_ok=True)
os.makedirs("eda_outputs/figures", exist_ok=True)

# Load cleaned data
posts = pd.read_csv("data/clean/Social_Engine_Posts_Cleaned.csv")
users = pd.read_csv("data/clean/Social_Engine_Users_Cleaned.csv")
held_out = pd.read_csv("data/clean/Social_Engine_Posts_EmptyText_HeldOut.csv")

print("Posts shape:", posts.shape)
print("Users shape:", users.shape)

# Convert timestamp
posts["timestamp_dt"] = pd.to_datetime(posts["timestamp_utc"])
posts["post_date"] = posts["timestamp_dt"].dt.date
posts["hour"] = posts["timestamp_dt"].dt.hour
posts["day_name"] = posts["timestamp_dt"].dt.day_name()
posts["month_year"] = posts["timestamp_dt"].dt.to_period("M").astype(str)

# Extract hashtags and brands
def extract_hashtags(text):
    if not isinstance(text, str):
        return []
    return re.findall(r"#\w+", text)

posts["hashtags"] = posts["text_content"].apply(extract_hashtags)

# Known brands in Social Engine: Nike, Adidas, Pepsi, Coca-Cola, Apple, Samsung, Google, Toyota, Amazon, Microsoft
brands = ["Nike", "Adidas", "Pepsi", "Coca-Cola", "Apple", "Samsung", "Google", "Toyota", "Amazon", "Microsoft"]
def detect_brand(text):
    if not isinstance(text, str):
        return "Unknown"
    for b in brands:
        if re.search(r"\b" + re.escape(b) + r"\b", text, re.IGNORECASE):
            return b
    return "Other/Generic"

posts["brand"] = posts["text_content"].apply(detect_brand)

# Merge posts with users
merged = posts.merge(users, on="user_id", how="left")
print("Merged shape:", merged.shape)

# Summary stats
eda_metrics = {}

# 1. Platform distribution
plat_dist = posts["platform"].value_counts().to_dict()
eda_metrics["platform_distribution"] = plat_dist

# 2. Engagement statistics by platform
eng_by_platform = posts.groupby("platform")[["likes", "shares", "comments"]].agg(["mean", "median", "std", "count"])
print("\n--- Engagement by Platform ---")
print(eng_by_platform)

# 3. Brand mentions and engagement
brand_stats = posts.groupby("brand")[["likes", "shares", "comments"]].agg({
    "likes": ["count", "mean", "median"],
    "shares": ["mean", "median"],
    "comments": ["mean", "median"]
})
print("\n--- Brand Stats ---")
print(brand_stats)

# 4. Correlation matrix
numeric_cols = ["likes", "shares", "comments"]
corr = posts[numeric_cols].corr().to_dict()
eda_metrics["correlation_matrix"] = corr

# 5. User analysis
top_locations = merged["location"].value_counts().head(10).to_dict()
top_languages = merged["language"].value_counts().to_dict()
eda_metrics["top_locations"] = top_locations
eda_metrics["top_languages"] = top_languages

# 6. Follower tiers vs engagement
merged["follower_tier"] = pd.qcut(merged["follower_count"], q=4, labels=["Low (Q1)", "Medium-Low (Q2)", "Medium-High (Q3)", "High (Q4)"])
tier_eng = merged.groupby("follower_tier", observed=False)[["likes", "shares", "comments", "follower_count"]].mean().to_dict()
eda_metrics["engagement_by_follower_tier"] = tier_eng

# 7. Temporal distribution
monthly_posts = posts["month_year"].value_counts().sort_index().to_dict()
eda_metrics["monthly_posts"] = monthly_posts

# Save EDA metrics to JSON
with open("eda_outputs/eda_summary_metrics.json", "w") as f:
    json.dump(eda_metrics, f, indent=2, default=str)

# Generate Plots
sns.set_theme(style="whitegrid")

# Plot 1: Platform Post Count & Likes
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
sns.countplot(data=posts, x="platform", order=posts["platform"].value_counts().index, ax=ax[0], palette="viridis")
ax[0].set_title("Post Volume by Platform")
ax[0].set_xlabel("Platform")
ax[0].set_ylabel("Number of Posts")
ax[0].tick_params(axis='x', rotation=30)

sns.boxplot(data=posts, x="platform", y="likes", order=posts["platform"].value_counts().index, ax=ax[1], palette="magma")
ax[1].set_title("Likes Distribution by Platform")
ax[1].set_xlabel("Platform")
ax[1].set_ylabel("Likes")
ax[1].tick_params(axis='x', rotation=30)
plt.tight_layout()
plt.savefig("eda_outputs/figures/fig1_platform_engagement.png", dpi=300)
plt.close()

# Plot 2: Brand Distribution & Share Volume
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
sns.countplot(data=posts, x="brand", order=posts["brand"].value_counts().index, ax=ax[0], palette="crest")
ax[0].set_title("Post Mentions by Brand")
ax[0].set_xlabel("Brand")
ax[0].tick_params(axis='x', rotation=45)

sns.barplot(data=posts, x="brand", y="shares", order=posts["brand"].value_counts().index, ax=ax[1], palette="flare", errorbar=None)
ax[1].set_title("Average Shares per Brand")
ax[1].set_xlabel("Brand")
ax[1].tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.savefig("eda_outputs/figures/fig2_brand_analysis.png", dpi=300)
plt.close()

# Plot 3: Temporal Activity Timeline
plt.figure(figsize=(12, 5))
monthly_series = posts["month_year"].value_counts().sort_index()
sns.lineplot(x=monthly_series.index, y=monthly_series.values, marker="o", color="#2b5c8f", linewidth=2.5)
plt.title("Monthly Post Intake Volume Timeline")
plt.xlabel("Month")
plt.ylabel("Post Count")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("eda_outputs/figures/fig3_timeline.png", dpi=300)
plt.close()

# Plot 4: Correlation Heatmap
plt.figure(figsize=(6, 5))
corr_matrix = posts[["likes", "shares", "comments"]].corr()
sns.heatmap(corr_matrix, annot=True, cmap="Blues", vmin=-1, vmax=1, fmt=".3f")
plt.title("Engagement Correlation Matrix (Likes, Shares, Comments)")
plt.tight_layout()
plt.savefig("eda_outputs/figures/fig4_correlation.png", dpi=300)
plt.close()

print("\nEDA completed successfully! Generated figures and metrics in eda_outputs/")
