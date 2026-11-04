// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.

using CaeMesh;
using System;
using System.Linq;

namespace FileInOut.Input
{
    internal static partial class GeometryMetadataReader
    {
        public static void ApplyCanonicalMeasurements(BasePart part)
        {
            GeometryMetadata metadata = part?.GeometryMetadata;
            VisualizationData visualization = part?.Visualization;
            if (metadata == null || visualization == null) return;
            //
            GeometryMetadataEntity[] faces = metadata.GetEntities("face");
            GeometryMetadataEntity[] edges = metadata.GetEntities("edge");
            if (visualization.FaceAreas != null)
            {
                foreach (GeometryMetadataEntity face in faces)
                {
                    double[] values;
                    int index = face.Id - 1;
                    if (index >= 0 && index < visualization.FaceAreas.Length &&
                        face.TryGetCanonicalNumbers("area", out values) && values.Length == 1)
                        visualization.FaceAreas[index] = values[0];
                }
            }
            if (visualization.EdgeLengths != null)
            {
                foreach (GeometryMetadataEntity edge in edges)
                {
                    double[] values;
                    int index = edge.Id - 1;
                    if (index >= 0 && index < visualization.EdgeLengths.Length &&
                        edge.TryGetCanonicalNumbers("length", out values) && values.Length == 1)
                        visualization.EdgeLengths[index] = values[0];
                }
            }
            ApplyBoundingBox(part, faces.Length > 0 ? faces : edges);
            //
            GeometryMetadataEntity[] solids = metadata.GetEntities("solid");
            if (solids.Length > 0) ApplySolidMassProperties(part, solids);
            else ApplyShellMassProperties(part, metadata.GetEntities("shell"));
        }
        private static void ApplyBoundingBox(BasePart part, GeometryMetadataEntity[] entities)
        {
            double[] bounds = null;
            foreach (GeometryMetadataEntity entity in entities)
            {
                double[] oneBounds;
                if (!entity.TryGetNumbers("bounding_box", out oneBounds) || oneBounds.Length != 6 ||
                    oneBounds.Any(value => Double.IsNaN(value) || Double.IsInfinity(value)) ||
                    oneBounds[0] > oneBounds[1] || oneBounds[2] > oneBounds[3] ||
                    oneBounds[4] > oneBounds[5]) continue;
                if (bounds == null) bounds = oneBounds.ToArray();
                else
                {
                    bounds[0] = Math.Min(bounds[0], oneBounds[0]);
                    bounds[1] = Math.Max(bounds[1], oneBounds[1]);
                    bounds[2] = Math.Min(bounds[2], oneBounds[2]);
                    bounds[3] = Math.Max(bounds[3], oneBounds[3]);
                    bounds[4] = Math.Min(bounds[4], oneBounds[4]);
                    bounds[5] = Math.Max(bounds[5], oneBounds[5]);
                }
            }
            if (bounds != null) part.BoundingBox = new BoundingBox(bounds);
        }
        private static void ApplySolidMassProperties(BasePart part, GeometryMetadataEntity[] solids)
        {
            double volume = 0;
            double area = 0;
            double[] firstMoment = new double[3];
            double[,] inertiaAtOrigin = new double[3, 3];
            foreach (GeometryMetadataEntity solid in solids)
            {
                double[] oneVolume;
                double[] center;
                double[] inertia;
                if (!solid.TryGetCanonicalNumbers("volume", out oneVolume) || oneVolume.Length != 1 ||
                    !solid.TryGetCanonicalNumbers("center_of_mass", out center) || center.Length != 3) continue;
                double value = oneVolume[0];
                volume += value;
                for (int i = 0; i < 3; i++) firstMoment[i] += value * center[i];
                double[] oneArea;
                if (solid.TryGetCanonicalNumbers("surface_area", out oneArea) && oneArea.Length == 1) area += oneArea[0];
                if (solid.TryGetCanonicalNumbers("inertia_at_center_of_mass", out inertia) && inertia.Length == 9)
                {
                    double radiusSquared = center[0] * center[0] + center[1] * center[1] + center[2] * center[2];
                    for (int row = 0; row < 3; row++)
                    {
                        for (int column = 0; column < 3; column++)
                        {
                            double shift = value * ((row == column ? radiusSquared : 0) -
                                                    center[row] * center[column]);
                            inertiaAtOrigin[row, column] += inertia[3 * row + column] + shift;
                        }
                    }
                }
            }
            if (volume <= 0) return;
            //
            PartMassProperties properties = new PartMassProperties(true);
            properties.Volume = volume;
            properties.Area = area;
            for (int i = 0; i < 3; i++) properties.CenterOfMass[i] = firstMoment[i] / volume;
            double centerRadiusSquared = properties.CenterOfMass.Sum(value => value * value);
            for (int row = 0; row < 3; row++)
            {
                for (int column = 0; column < 3; column++)
                {
                    properties.InertiaMatrixOrigin[row][column] = inertiaAtOrigin[row, column];
                    double shift = volume * ((row == column ? centerRadiusSquared : 0) -
                                             properties.CenterOfMass[row] * properties.CenterOfMass[column]);
                    properties.InertiaMatrixCG[row][column] = inertiaAtOrigin[row, column] - shift;
                }
            }
            part.MassProperties = properties;
        }
        private static void ApplyShellMassProperties(BasePart part, GeometryMetadataEntity[] shells)
        {
            double area = 0;
            double[] firstMoment = new double[3];
            foreach (GeometryMetadataEntity shell in shells)
            {
                double[] oneArea;
                double[] centroid;
                if (!shell.TryGetCanonicalNumbers("area", out oneArea) || oneArea.Length != 1 ||
                    !shell.TryGetCanonicalNumbers("centroid", out centroid) || centroid.Length != 3) continue;
                area += oneArea[0];
                for (int i = 0; i < 3; i++) firstMoment[i] += oneArea[0] * centroid[i];
            }
            if (area <= 0) return;
            //
            PartMassProperties properties = part.MassProperties;
            properties.Area = area;
            properties.CenterOfMass = firstMoment.Select(value => value / area).ToArray();
            part.MassProperties = properties;
        }
    }
}
