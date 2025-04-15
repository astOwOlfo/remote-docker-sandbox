import os
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from beartype import beartype
from typing import List, Optional, Union

@beartype
def plot_call_timestamps(server_urls: Optional[List[str]] = None, save_filename: Optional[str] = None) -> None:
    """
    Fetch call timestamps from specified servers and plot them using Plotly.
    
    Args:
        server_urls: List of server URLs to fetch timestamps from. If None, reads from REMOTE_DOCKER_SANDBOX_SERVER_URL env var.
        save_filename: If provided, saves the figure to this file as HTML. Otherwise, shows the figure.
    """
    # Get server URLs from environment variable if not provided
    if server_urls is None:
        env_urls = os.environ.get("REMOTE_DOCKER_SANDBOX_SERVER_URL")
        if not env_urls:
            raise ValueError("No server URLs provided and REMOTE_DOCKER_SANDBOX_SERVER_URL environment variable not set")
        server_urls = [url.strip() for url in env_urls.split(",")]
    
    # Define colors for different servers (will cycle if more servers than colors)
    colors = ['blue', 'red', 'green', 'purple', 'orange', 'brown', 'pink', 'gray', 'olive', 'cyan']
    
    # Create subplots (one row for each server)
    fig = make_subplots(rows=len(server_urls), shared_xaxes=True, 
                        vertical_spacing=0.02,
                        subplot_titles=[f"Server: {url}" for url in server_urls])
    
    # For each server, fetch and plot the data
    for i, server_url in enumerate(server_urls):
        color = colors[i % len(colors)]
        row = i + 1
        
        try:
            # Fetch timestamps from server
            response = requests.get(f"{server_url}/get_call_timestamps")
            response.raise_for_status()  # Raise exception for 4xx/5xx responses
            
            timestamps = response.json()
            
            # Plot each timestamp as a line
            for j, ts in enumerate(timestamps):
                start = ts["start"]
                end = ts["end"]
                duration = end - start
                
                # Add line for this timestamp
                fig.add_trace(
                    go.Scatter(
                        x=[start, end],
                        y=[j, j],
                        mode='lines',
                        line=dict(color=color, width=2),
                        name=f"{server_url} - Call {j}",
                        showlegend=False
                    ),
                    row=row, col=1
                )
        
        except Exception as e:
            print(f"Error fetching data from {server_url}: {e}")
    
    # Update layout
    fig.update_layout(
        title="Call Timestamps by Server",
        xaxis_title="Time (seconds)",
        height=200 * len(server_urls),  # Adjust height based on number of servers
        margin=dict(l=50, r=20, t=50, b=50),
    )
    
    # For each subplot, hide y-axis labels as they're just indices
    for i in range(1, len(server_urls) + 1):
        fig.update_yaxes(showticklabels=False, row=i, col=1)
    
    # Either save or show the figure
    if save_filename:
        fig.write_html(save_filename)
        print(f"Figure saved to {save_filename}")
    else:
        fig.show()


if __name__ == "__main__":
    plot_call_timestamps()
