"""Coatings Module

The coatings module contains classes for modeling optical coatings.

Kramer Harrison, 2024
"""

from abc import ABC, abstractmethod

import optiland.backend as be
from optiland.jones import JonesFresnel
from optiland.materials import BaseMaterial
from optiland.rays import RealRays


class BaseCoating(ABC):
    """Base class for coatings.

    This class defines the basic structure and behavior of a coating.

    Methods:
        interact: Performs an interaction with the coating.
        reflect: Abstract method to handle reflection interaction with the coating.
        transmit: Abstract method to handle transmission interaction with the coating.

    """

    _registry = {}

    def __init_subclass__(cls, **kwargs):
        """Automatically register subclasses."""
        super().__init_subclass__(**kwargs)
        BaseCoating._registry[cls.__name__] = cls

    def interact(
        self,
        rays: RealRays,
        reflect: bool = False,
        nx: be.ndarray = None,
        ny: be.ndarray = None,
        nz: be.ndarray = None,
    ):
        """Performs an interaction with the coating.

        Args:
            rays (RealRays): The rays incident on the coating.
            reflect (bool, optional): Flag indicating whether to perform
                reflection (True) or transmission (False). Defaults to False.
            nx (be.ndarray, optional): The x-component of the surface normal vectors.
            ny (be.ndarray, optional): The y-component of the surface normal vectors.
            nz (be.ndarray, optional): The z-component of the surface normal vectors.

        Returns:
            rays (RealRays): The rays after the interaction.

        """
        if reflect:
            return self.reflect(rays, nx, ny, nz)
        return self.transmit(rays, nx, ny, nz)

    def _compute_aoi(self, rays, nx, ny, nz):
        """Computes the angle of incidence for the given rays and surface normals.

        Args:
            rays (RealRays): The incident rays.
            nx (be.ndarray): The x-component of the surface normal vectors at each ray's
                intersection point.
            ny (be.ndarray): The y-component of the surface normal vectors at each ray's
                intersection point.
            nz (be.ndarray): The z-component of the surface normal vectors at each ray's
                intersection point.

        Returns:
            be.ndarray: The angle of incidence for each ray.

        """
        dot = be.abs(nx * rays.L0 + ny * rays.M0 + nz * rays.N0)
        dot = be.clip(dot, -1, 1)  # required due to numerical precision
        return be.arccos(dot)

    @abstractmethod
    def reflect(
        self,
        rays: RealRays,
        nx: be.ndarray = None,
        ny: be.ndarray = None,
        nz: be.ndarray = None,
    ):
        """Abstract method to handle reflection interaction.

        Args:
            rays (RealRays): The rays incident on the coating.
            nx (be.ndarray, optional): The x-component of the surface normal vectors.
            ny (be.ndarray, optional): The y-component of the surface normal vectors.
            nz (be.ndarray, optional): The z-component of the surface normal vectors.

        Returns:
            RealRays: The rays after reflection.

        """
        # pragma: no cover

    @abstractmethod
    def transmit(
        self,
        rays: RealRays,
        nx: be.ndarray = None,
        ny: be.ndarray = None,
        nz: be.ndarray = None,
    ):
        """Abstract method to handle transmission interaction.

        Args:
            rays (RealRays): The rays incident on the coating.
            nx (be.ndarray, optional): The x-component of the surface normal vectors.
            ny (be.ndarray, optional): The y-component of the surface normal vectors.
            nz (be.ndarray, optional): The z-component of the surface normal vectors.

        Returns:
            RealRays: The rays after transmission.

        """
        # pragma: no cover

    def to_dict(self):  # pragma: no cover
        """Converts the coating to a dictionary.

        Returns:
            dict: The dictionary representation of the coating.

        """
        return {
            "type": self.__class__.__name__,
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a coating from a dictionary.

        Args:
            data (dict): The dictionary representation of the coating.

        Returns:
            BaseCoating: The coating created from the dictionary.

        """
        coating_type = data["type"]
        return cls._registry[coating_type].from_dict(data)


class SimpleCoating(BaseCoating):
    """A simple coating class that represents a coating with given transmittance
    and reflectance.

    Args:
        transmittance (float): The transmittance of the coating.
        reflectance (float, optional): The reflectance of the coating.
            Defaults to 0.

    Attributes:
        transmittance (float): The transmittance of the coating.
        reflectance (float): The reflectance of the coating.
        absorptance (float): The absorptance of the coating, calculated
            as 1 - reflectance - transmittance.

    Methods:
        reflect(rays: RealRays, nx: be.ndarray = None, ny: be.ndarray = None,
            nz: be.ndarray = None) -> RealRays: Reflects the rays based on the
            reflectance of the coating.
        transmit(rays: RealRays, nx: be.ndarray = None, ny: be.ndarray = None,
            nz: be.ndarray = None) -> RealRays: Transmits the rays based on the
            transmittance of the coating.

    """

    def __init__(self, transmittance, reflectance=0):
        self.transmittance = transmittance
        self.reflectance = reflectance
        self.absorptance = 1 - reflectance - transmittance

    def reflect(
        self,
        rays: RealRays,
        nx: be.ndarray = None,
        ny: be.ndarray = None,
        nz: be.ndarray = None,
    ):
        """Reflects the rays based on the reflectance of the coating.

        Args:
            rays (RealRays): The rays incident on the coating.
            nx (be.ndarray, optional): The x-component of the surface normal vectors.
            ny (be.ndarray, optional): The y-component of the surface normal vectors.
            nz (be.ndarray, optional): The z-component of the surface normal vectors.

        Returns:
            RealRays: The rays after reflection.

        """
        rays.i = rays.i * self.reflectance
        return rays

    def transmit(
        self,
        rays: RealRays,
        nx: be.ndarray = None,
        ny: be.ndarray = None,
        nz: be.ndarray = None,
    ):
        """Transmits the rays through the coating by multiplying their intensity
        with the transmittance.

        Args:
            rays (RealRays): The rays incident on the coating.
            nx (be.ndarray, optional): The x-component of the surface normal vectors.
            ny (be.ndarray, optional): The y-component of the surface normal vectors.
            nz (be.ndarray, optional): The z-component of the surface normal vectors.

        Returns:
            RealRays: The rays after transmission.

        """
        rays.i = rays.i * self.transmittance
        return rays

    def to_dict(self):
        """Converts the coating to a dictionary.

        Returns:
            dict: The dictionary representation of the coating.

        """
        return {
            "type": self.__class__.__name__,
            "transmittance": self.transmittance,
            "reflectance": self.reflectance,
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a coating from a dictionary.

        Args:
            data (dict): The dictionary representation of the coating.

        Returns:
            BaseCoating: The coating created from the dictionary.

        """
        return cls(data["transmittance"], data["reflectance"])


class BaseCoatingPolarized(BaseCoating, ABC):
    """A base class for polarized coatings.

    This class inherits from the `BaseCoating` class and the `ABC`
    (Abstract Base Class) module.

    Methods:
        reflect(rays, nx, ny, nz): Reflects the rays off the coating.
        transmit(rays, nx, ny, nz): Transmits the rays through the coating.

    """

    def reflect(
        self,
        rays: RealRays,
        nx: be.ndarray = None,
        ny: be.ndarray = None,
        nz: be.ndarray = None,
    ):
        """Reflects the rays off the coating.

        Args:
            rays (RealRays): The rays to be reflected.
            nx (be.ndarray, optional): The x-component of the surface normal vector.
            ny (be.ndarray, optional): The y-component of the surface normal vector.
            nz (be.ndarray, optional): The z-component of the surface normal vector.

        Returns:
            RealRays: The updated rays after reflection.

        """
        aoi = self._compute_aoi(rays, nx, ny, nz)
        jones = self.jones.calculate_matrix(rays, reflect=True, aoi=aoi)
        rays.update(jones)
        return rays

    def transmit(
        self,
        rays: RealRays,
        nx: be.ndarray = None,
        ny: be.ndarray = None,
        nz: be.ndarray = None,
    ):
        """Transmits the rays through the coating.

        Args:
            rays (RealRays): The rays to be transmitted.
            nx (be.ndarray, optional): The x-component of the surface normal vector.
            ny (be.ndarray, optional): The y-component of the surface normal vector.
            nz (be.ndarray, optional): The z-component of the surface normal vector.

        Returns:
            RealRays: The updated rays after transmission through a surface.

        """
        aoi = self._compute_aoi(rays, nx, ny, nz)
        jones = self.jones.calculate_matrix(rays, reflect=False, aoi=aoi)
        rays.update(jones)
        return rays

    def to_dict(self):  # pragma: no cover
        """Converts the coating to a dictionary.

        Returns:
            dict: The dictionary representation of the coating.

        """
        return {
            "type": self.__class__.__name__,
            "material_pre": self.material_pre.to_dict(),
            "material_post": self.material_post.to_dict(),
        }

    @classmethod
    def from_dict(cls, data):  # pragma: no cover
        """Creates a coating from a dictionary.

        Args:
            data (dict): The dictionary representation of the coating.

        Returns:
            BaseCoating: The coating created from the dictionary.

        """
        return cls(data["material_pre"], data["material_post"])


class FresnelCoating(BaseCoatingPolarized):
    """Represents a Fresnel coating for polarized light.

    This class inherits from the BaseCoatingPolarized class and provides
    interaction functionality for polarized light with uncoated surfaces.
    In general, this updates ray intensities based on the Fresnel equations
    on a surface.

    Attributes:
        material_pre (str): The material before the coating.
        material_post (str): The material after the coating.
        jones (JonesFresnel): The JonesFresnel object, which calculates the
            Jones matrices for given ray properties.

    """

    def __init__(self, material_pre, material_post):
        self.material_pre = material_pre
        self.material_post = material_post

        self.jones = JonesFresnel(material_pre, material_post)

    def to_dict(self):
        """Converts the coating to a dictionary.

        Returns:
            dict: The dictionary representation of the coating.

        """
        return {
            "type": self.__class__.__name__,
            "material_pre": self.material_pre.to_dict(),
            "material_post": self.material_post.to_dict(),
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a coating from a dictionary.

        Args:
            data (dict): The dictionary representation of the coating.

        Returns:
            BaseCoating: The coating created from the dictionary.

        """
        return cls(
            BaseMaterial.from_dict(data["material_pre"]),
            BaseMaterial.from_dict(data["material_post"]),
        )
