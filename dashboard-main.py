import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt
import numpy as np

image_url = "https://upload.wikimedia.org/wikipedia/commons/0/03/Flag_of_Washington%2C_D.C.svg"

# Page configuration
st.set_page_config(layout="wide")

st.image(image_url, width=100)
st.title("Washington D.C. Airbnb Dashboard") 
st.write("Explore Airbnb listings across Washington, D.C.")

# Load Airbnb data
df = pd.read_csv("archive/Airbnb Listings.csv")
df = df[df["price"] < 1000]  # Filter out extreme prices for better visualization
df = df[df["minimum_nights"] < 40]  # Filter out extreme minimum nights for better visualization

# -----------------------
# Metrics Section
# -----------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Listings", len(df))
col2.metric("Unique Neighborhoods", df["neighbourhood"].nunique())

if "price" in df.columns:
    col3.metric("Average Price", f"${df['price'].mean():.0f}")

# -----------------------
# Raw Data
# -----------------------
st.subheader("Raw Airbnb Listings Data")
st.dataframe(df)

# -----------------------
# Prepare Map Data
# -----------------------
map_df = df[["latitude", "longitude"]].dropna()

view_state = pdk.ViewState(
    latitude=map_df["latitude"].mean(),
    longitude=map_df["longitude"].mean(),
    zoom=11,
    pitch=50,
)

# -----------------------
# Chart Data
# -----------------------
top_neighbourhoods = (
    df["neighbourhood"]
    .value_counts()
    .head(10)
    .reset_index()
)

top_neighbourhoods.columns = ["Neighbourhood", "Listings"]

avg_price = (
    df.groupby("neighbourhood")["price"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)

avg_price.columns = ["Neighbourhood", "Average Price"]

chart = alt.Chart(top_neighbourhoods).mark_bar(
    color="#4CAF50"
).encode(
    x=alt.X("Listings:Q", title="Number of Listings"),
    y=alt.Y("Neighbourhood:N", sort="-x"),
    tooltip=["Neighbourhood", "Listings"]
).properties(
    title="Top 10 Neighborhoods with Most Airbnb Listings"
)

price_chart = alt.Chart(avg_price).mark_bar(
    color="#FF7F50"
).encode(
    x=alt.X("Average Price:Q", title="Average Price ($)"),
    y=alt.Y("Neighbourhood:N", sort="-x"),
    tooltip=["Neighbourhood", "Average Price"]
).properties(
    title="Average Airbnb Price by Neighborhood"
)

# Popular attractions with coordinates
attractions = {
    "White House": (38.8977, -77.0365),
    "Washington Monument": (38.8895, -77.0353),
    "Jefferson Memorial": (38.8814, -77.0365),
    "Capitol Building": (38.8899, -77.0091),
    "Smithsonian Museum": (38.8887, -77.0260),
    "Walter Washington Convention Center": (38.9053, -77.0222),
    "Capital One Arena": (38.8981, -77.0209),
    "Nationals Park": (38.8730, -77.0074),
    "Navy Yard": (38.8763, -77.0050),
    "Audi Field": (38.8682, -77.0129),
    "Georgetown University": (38.9076, -77.0723),
    "Howard University": (38.9227, -77.0194),
    "George Washington University": (38.8997, -77.0470),
    "Reagan National Airport": (38.8512, -77.0402),
    "The Anthem": (38.8780, -77.0183)
}

# Haversine formula to calculate distance between two lat/lon points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km

    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    return R * c

# -----------------------
# Map + Chart Layout
# -----------------------
col1, col2 = st.columns([2, 1])

# Maps and charts in the left column
with col1:
    st.subheader("Airbnb Listing Density Map")

    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            initial_view_state=view_state,
            layers=[
                pdk.Layer(
                    "HexagonLayer",
                    data=map_df,
                    get_position="[longitude, latitude]",
                    radius=200,
                    elevation_scale=4,
                    elevation_range=[0, 1000],
                    pickable=True,
                    extruded=True,
                )
            ],
        )
    )

    st.subheader("Price Distribution by Room Type")

    room_price_chart = alt.Chart(df).mark_circle(
        size=60,
        opacity=0.4,
        color="#1f77b4"
    ).encode(
        x=alt.X("room_type:N", title="Room Type"),
        y=alt.Y("price:Q", title="Price ($)"),
        tooltip=["room_type", "price", "minimum_nights"]
    ).properties(
        title="Price vs Room Type"
    )

    st.altair_chart(room_price_chart, use_container_width=True)

    st.subheader("Price vs Minimum Nights")

    price_nights_chart = alt.Chart(df).mark_circle(
        size=60,
        opacity=0.4,
        color="#FF5733"
    ).encode(
        x=alt.X("minimum_nights:Q", title="Minimum Nights"),
        y=alt.Y("price:Q", title="Price ($)"),
        tooltip=["room_type", "price", "minimum_nights"],
        color=alt.Color("room_type:N", title="Room Type")
    ).properties(
        title="Price vs Minimum Nights"
    )

    st.altair_chart(price_nights_chart, use_container_width=True)

# Charts in the right column
with col2:
    st.subheader("Top Neighborhoods")
    st.altair_chart(chart, use_container_width=True)

    st.subheader("Average Price by Neighborhood")
    st.altair_chart(price_chart, use_container_width=True)

st.header("Airbnbs Near Major Attractions (1 km)")

# Calculate distance from each listing to each attraction and display nearby listings
for attraction, (lat, lon) in attractions.items():

    df["distance"] = haversine(df["latitude"], df["longitude"], lat, lon)
    nearby = df[df["distance"] <= 1]

    if not nearby.empty:

        col1, col2 = st.columns([1,1])

        with col1:
            st.subheader(f"{attraction} ({len(nearby)} listings)")

            st.dataframe(
                nearby[["name","neighbourhood","room_type","price","minimum_nights","distance"]]
                .sort_values("distance")
                .reset_index(drop=True)
            )

        with col2:

            price_box = alt.Chart(nearby).mark_boxplot().encode(
                y=alt.Y("price:Q", title="Price ($)")
            ).properties(
                title=f"Price Distribution Near {attraction}"
            )

            st.altair_chart(price_box, use_container_width=True)