"""
Chart Generator Service

Matplotlib-based chart generation service for reports.
Responsible for creating scatter plots, line plots, heatmaps, and histograms.
"""

import io
import logging
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Backend não-interativo
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Import ReportConfig from parent module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from report_generator import ReportConfig

log = logging.getLogger(__name__)


class ChartGenerator:
    """
    Chart generation service using Matplotlib.

    Responsibilities:
    - Create scatter plots (ex: tension map)
    - Create line plots (ex: trend charts)
    - Create heatmaps
    - Create histograms
    - Save charts as images for PDF embedding

    This service isolates all Matplotlib-specific code, making it easier
    to test and maintain report builders.
    """

    def __init__(self, config: ReportConfig):
        """
        Initialize chart generator with report configuration.

        Args:
            config: Report configuration with colors, logo, etc.
        """
        self.config = config

    # ======================================================================== #
    # CHART CREATION METHODS
    # ======================================================================== #

    def create_scatter_plot(
        self,
        x_data: List[float],
        y_data: List[float],
        color_data: List[str] = None,
        labels: List[str] = None,
        title: str = "",
        xlabel: str = "X",
        ylabel: str = "Y",
        figsize: Tuple[float, float] = (4, 3),
        dpi: int = 100,
        point_size: int = 100,
        show_grid: bool = True,
        show_values: bool = False,
        value_format: str = "{:.1f}",
        show_legend: bool = True,
    ) -> plt.Figure:
        """
        Create scatter plot (ex: tension map).

        Args:
            x_data: X coordinates
            y_data: Y coordinates
            color_data: List of status strings (OK, WARNING, NOK)
            labels: Optional labels for each point
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size (width, height) in inches
            dpi: Dots per inch
            point_size: Size of scatter points
            show_grid: Show grid lines
            show_values: Show value annotations on points
            value_format: Format string for values
            show_legend: Show status legend

        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # Get status colors
        status_colors = self._get_status_colors()

        # Map status strings to colors
        if color_data:
            point_colors = [status_colors.get(s.upper(), '#3498db') for s in color_data]
        else:
            point_colors = '#3498db'

        # Create scatter plot
        scatter = ax.scatter(
            x_data,
            y_data,
            c=point_colors,
            s=point_size,
            edgecolors='black',
            linewidths=0.5
        )

        # Add value annotations
        if show_values and labels:
            for x, y, label in zip(x_data, y_data, labels):
                ax.annotate(
                    label,
                    (x, y),
                    textcoords="offset points",
                    xytext=(0, 8),
                    ha='center',
                    fontsize=7
                )

        # Labels and title
        ax.set_xlabel(xlabel, fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        if title:
            ax.set_title(title, fontsize=10, fontweight='bold')

        # Grid
        if show_grid:
            ax.grid(True, alpha=0.3)

        # Equal aspect ratio
        ax.set_aspect('equal', adjustable='datalim')

        # Legend
        if show_legend and color_data:
            legend_elements = [
                patches.Patch(
                    facecolor=status_colors['OK'],
                    edgecolor='black',
                    label='OK'
                ),
                patches.Patch(
                    facecolor=status_colors['WARNING'],
                    edgecolor='black',
                    label='WARNING'
                ),
                patches.Patch(
                    facecolor=status_colors['NOK'],
                    edgecolor='black',
                    label='NOK'
                ),
            ]
            ax.legend(handles=legend_elements, loc='upper right', fontsize=7)

        plt.tight_layout()
        return fig

    def create_line_plot(
        self,
        x_data: List,
        y_data: List[float],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        figsize: Tuple[float, float] = (7, 3),
        dpi: int = 100,
        color: str = None,
        show_grid: bool = True,
        marker: str = 'o',
        line_width: float = 2,
        marker_size: int = 6,
        fill_area: bool = True,
        show_trendline: bool = False,
    ) -> plt.Figure:
        """
        Create line plot (ex: trend chart).

        Args:
            x_data: X coordinates (can be dates or indices)
            y_data: Y values
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size in inches
            dpi: Dots per inch
            color: Line color (hex code, None = use theme primary)
            show_grid: Show grid lines
            marker: Marker style
            line_width: Line width
            marker_size: Marker size
            fill_area: Fill area under line
            show_trendline: Show linear trend line

        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # Use theme primary color if none specified
        if color is None:
            r, g, b = self.config.primary_color
            color = f'#{r:02x}{g:02x}{b:02x}'

        # Plot line
        ax.plot(
            range(len(y_data)),
            y_data,
            f'{color}-{marker}',
            linewidth=line_width,
            markersize=marker_size
        )

        # Fill area under line
        if fill_area:
            ax.fill_between(range(len(y_data)), y_data, alpha=0.3)

        # Labels and title
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=9)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=9)
        if title:
            ax.set_title(title, fontsize=10, fontweight='bold')

        # Grid
        if show_grid:
            ax.grid(True, alpha=0.3)

        # Trend line
        if show_trendline and len(y_data) >= 3:
            z = np.polyfit(range(len(y_data)), y_data, 1)
            p = np.poly1d(z)
            ax.plot(
                range(len(y_data)),
                p(range(len(y_data))),
                'r--',
                alpha=0.7,
                label='Tendência'
            )
            ax.legend(fontsize=8)

        plt.tight_layout()
        return fig

    def create_heatmap(
        self,
        data: np.ndarray,
        x_labels: List[str] = None,
        y_labels: List[str] = None,
        title: str = "",
        cmap: str = "RdYlGn",
        figsize: Tuple[float, float] = (6, 4),
        dpi: int = 100,
        show_values: bool = True,
        value_format: str = "{:.2f}",
        colorbar_label: str = "",
    ) -> plt.Figure:
        """
        Create heatmap.

        Args:
            data: 2D numpy array of values
            x_labels: Optional X-axis labels
            y_labels: Optional Y-axis labels
            title: Chart title
            cmap: Colormap name
            figsize: Figure size in inches
            dpi: Dots per inch
            show_values: Show value annotations in cells
            value_format: Format string for values
            colorbar_label: Label for colorbar

        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # Create heatmap
        im = ax.imshow(data, cmap=cmap, aspect='auto')

        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        if colorbar_label:
            cbar.set_label(colorbar_label, rotation=270, labelpad=15)

        # Axis labels
        if x_labels:
            ax.set_xticks(range(len(x_labels)))
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
        if y_labels:
            ax.set_yticks(range(len(y_labels)))
            ax.set_yticklabels(y_labels)

        # Title
        if title:
            ax.set_title(title, fontsize=10, fontweight='bold')

        # Value annotations
        if show_values:
            for i in range(data.shape[0]):
                for j in range(data.shape[1]):
                    text = ax.text(
                        j,
                        i,
                        value_format.format(data[i, j]),
                        ha="center",
                        va="center",
                        color="black",
                        fontsize=8
                    )

        plt.tight_layout()
        return fig

    def create_histogram(
        self,
        data: List[float],
        bins: int = 20,
        title: str = "",
        xlabel: str = "Value",
        ylabel: str = "Frequency",
        figsize: Tuple[float, float] = (6, 4),
        dpi: int = 100,
        color: str = None,
        alpha: float = 0.7,
        edge_color: str = "black",
        show_stats: bool = False,
    ) -> plt.Figure:
        """
        Create histogram.

        Args:
            data: List of values
            bins: Number of bins
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size in inches
            dpi: Dots per inch
            color: Bar color (None = use theme primary)
            alpha: Bar transparency
            edge_color: Edge color
            show_stats: Show mean and std on plot

        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # Use theme primary color if none specified
        if color is None:
            r, g, b = self.config.primary_color
            color = f'#{r:02x}{g:02x}{b:02x}'

        # Create histogram
        n, bins_edges, patches = ax.hist(
            data,
            bins=bins,
            color=color,
            alpha=alpha,
            edgecolor=edge_color
        )

        # Labels and title
        ax.set_xlabel(xlabel, fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        if title:
            ax.set_title(title, fontsize=10, fontweight='bold')

        # Grid
        ax.grid(True, alpha=0.3, axis='y')

        # Statistics
        if show_stats and data:
            mean = np.mean(data)
            std = np.std(data)
            ax.axvline(mean, color='red', linestyle='--', linewidth=2, label=f'Média: {mean:.2f}')
            ax.legend(fontsize=8)

        plt.tight_layout()
        return fig

    # ======================================================================== #
    # SAVE METHODS
    # ======================================================================== #

    def save_as_image(
        self,
        fig: plt.Figure,
        format: str = "png",
        dpi: int = 150,
        bbox_inches: str = "tight"
    ) -> io.BytesIO:
        """
        Save figure to BytesIO buffer (for PDF embedding).

        Args:
            fig: matplotlib Figure
            format: Image format (png, jpg, svg, pdf)
            dpi: Dots per inch
            bbox_inches: Bounding box setting

        Returns:
            BytesIO buffer with image data
        """
        buf = io.BytesIO()
        fig.savefig(buf, format=format, dpi=dpi, bbox_inches=bbox_inches)
        buf.seek(0)
        return buf

    def save_as_file(
        self,
        fig: plt.Figure,
        path: str,
        format: str = None,
        dpi: int = 150,
        bbox_inches: str = "tight"
    ) -> str:
        """
        Save figure to file.

        Args:
            fig: matplotlib Figure
            path: Output file path
            format: Image format (None = infer from extension)
            dpi: Dots per inch
            bbox_inches: Bounding box setting

        Returns:
            Path to saved file
        """
        fig.savefig(path, format=format, dpi=dpi, bbox_inches=bbox_inches)
        log.info(f"Gráfico salvo: {path}")
        return path

    def close(self, fig: plt.Figure) -> None:
        """
        Close figure to free memory.

        Args:
            fig: matplotlib Figure to close
        """
        plt.close(fig)

    # ======================================================================== #
    # UTILITY METHODS
    # ======================================================================== #

    def _get_status_colors(self) -> Dict[str, str]:
        """
        Get status color map (hex codes).

        Returns:
            Dictionary mapping status to hex color codes
        """
        return {
            'OK': '#2ecc71',      # Verde
            'WARNING': '#f1c40f', # Amarelo
            'WARN': '#f1c40f',
            'NOK': '#e74c3c',     # Vermelho
        }

    def apply_theme_colors(self, fig: plt.Figure) -> None:
        """
        Apply report theme colors to figure.

        Args:
            fig: matplotlib Figure to style
        """
        r, g, b = self.config.primary_color
        primary_color = f'#{r:02x}{g:02x}{b:02x}'

        # Apply to axes
        for ax in fig.get_axes():
            ax.spines['bottom'].set_color(primary_color)
            ax.spines['top'].set_color(primary_color)
            ax.spines['right'].set_color(primary_color)
            ax.spines['left'].set_color(primary_color)

    def create_status_legend(self) -> List[patches.Patch]:
        """
        Create status legend patches.

        Returns:
            List of matplotlib Patch objects for legend
        """
        status_colors = self._get_status_colors()
        return [
            patches.Patch(facecolor=status_colors['OK'], edgecolor='black', label='OK'),
            patches.Patch(facecolor=status_colors['WARNING'], edgecolor='black', label='WARNING'),
            patches.Patch(facecolor=status_colors['NOK'], edgecolor='black', label='NOK'),
        ]
