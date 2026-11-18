// PrePoMax - Copyright (C) 2016-2026 Matej Borovinšek
//
// Licensed under the terms defined in the LICENSE file located in the root directory of this source code.
//
// Source code: https://github.com/PrePoMax/PrePoMax
//
// Author: Matej Borovinšek
// Contributors:

using System;
using System.IO;

namespace CaeGlobals
{
    public static partial class Tools
    {
        private static readonly float _oneThird = 1f / 3f;
        private static readonly float _twoPiThirds = 2f * (float)Math.PI / 3f;
        private static readonly float _fourPiThirds = 4f * (float)Math.PI / 3f;
        public static bool IsFileLocked(string fileName)
        {
            FileInfo fileInfo = new FileInfo(fileName);
            FileStream stream = null;

            try
            {
                stream = fileInfo.Open(FileMode.Open, FileAccess.Read, FileShare.None);
            }
            catch (IOException)
            {
                // The file is unavailable because it is still being written to
                // or being processed by another thread or does not exist (has already been processed)
                return true;
            }
            finally
            {
                if (stream != null) stream.Close();
            }
            // File is not locked
            return false;
        }
        public static bool WaitForFileToUnlock(string fileName, long miliseconds)
        {
            DateTime start = DateTime.Now;
            while (IsFileLocked(fileName))
            {
                if ((DateTime.Now - start).TotalMilliseconds >= miliseconds) return false;
                System.Threading.Thread.Sleep(100);
            }
            return true;
        }
        public static string GetRandomString(int len)
        {
            var chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
            var stringChars = new char[len];
            var random = new Random();
            for (int i = 0; i < stringChars.Length; i++)
            {
                stringChars[i] = chars[random.Next(chars.Length)];
            }
            return new String(stringChars);
        }
        // Sort
        public static void Sort3_descending(ref float arr0, ref float arr1, ref float arr2)
        {
            float arr120;
            float arr121;

            // sort first two values
            if (arr0 > arr1)
            {
                arr120 = arr0;
                arr121 = arr1;
            } // if
            else
            {
                arr120 = arr1;
                arr121 = arr0;
            } // else

            // decide where to put arr12 and the third original value arr[ 3 ]
            if (arr121 > arr2)
            {
                arr0 = arr120;
                arr1 = arr121;
            } // if
            else if (arr2 > arr120)
            {
                arr0 = arr2;
                arr1 = arr120;
                arr2 = arr121;
            } // if
            else
            {
                arr0 = arr120;
                arr1 = arr2;
                arr2 = arr121;
            } // else
        }
        public static void Sort3_descending(ref double arr0, ref double arr1, ref double arr2)
        {
            double arr120;
            double arr121;

            // sort first two values
            if (arr0 > arr1)
            {
                arr120 = arr0;
                arr121 = arr1;
            } // if
            else
            {
                arr120 = arr1;
                arr121 = arr0;
            } // else

            // decide where to put arr12 and the third original value arr[ 3 ]
            if (arr121 > arr2)
            {
                arr0 = arr120;
                arr1 = arr121;
            } // if
            else if (arr2 > arr120)
            {
                arr0 = arr2;
                arr1 = arr120;
                arr2 = arr121;
            } // if
            else
            {
                arr0 = arr120;
                arr1 = arr2;
                arr2 = arr121;
            } // else
        }
        // Solve Qubic
        public static void SolveQubicEquationDepressedCubic(double a, double b, double c, double d,
                                                            ref double x1, ref double x2, ref double x3)
        {
            // https://en.wikipedia.org/wiki/Cubic_function
            // https://www.easycalculation.com/algebra/cubic-equation.php - check source
            double p;
            double q;
            double tmp1;
            double tmp2;
            double alpha;

            p = (3.0 * a * c - b * b) / (3.0 * a * a);
            if (p > 0)
            {
                // One root real, two are complex
                x1 = x2 = x3 = 0;
            }
            else if (p == 0)
            {
                // All roots real, at least two are equal.
                double term1 = b * _oneThird;
                double r = -(27f * d) + b * (9f * c - 2f * b * b);
                double r13 = (r < 0) ? -Math.Pow(-r, _oneThird) : Math.Pow(r, _oneThird);
                x1 = -term1 + 2f * r13;
                x2 = -(r13 + term1);
                x3 = x2;
            }
            else
            {
                q = (2.0 * b * b * b - 9.0 * a * b * c + 27.0 * a * a * d) / (27.0 * a * a * a);
                //
                tmp1 = (3.0 * q) / (2.0 * p) * Math.Sqrt(-3.0 / p);
                if (tmp1 > 1.0) tmp1 = 1.0;
                else if (tmp1 < -1.0) tmp1 = -1.0;
                alpha = 1.0 / 3.0 * Math.Acos(tmp1);
                //
                tmp1 = 2.0 * Math.Sqrt(-p / 3.0);
                tmp2 = b / (3.0 * a);
                x1 = tmp1 * Math.Cos(alpha) - tmp2;
                x2 = tmp1 * Math.Cos(alpha - 2.0 * Math.PI / 3.0) - tmp2;
                x3 = tmp1 * Math.Cos(alpha - 4.0 * Math.PI / 3.0) - tmp2;
            }
        }
        public static void SolveQubicEquationDepressedCubicF(float a, float b, float c, float d,
                                                             ref float x1, ref float x2, ref float x3)
        {
            // https://en.wikipedia.org/wiki/Cubic_function
            // https://www.easycalculation.com/algebra/cubic-equation.php - check source
            float p;
            float q;
            float tmp1;
            float tmp2;
            float alpha;
            //
            p = (3f * a * c - b * b) / (3f * a * a);
            if (p > 0)
            {
                // One root real, two are complex
                x1 = x2 = x3 = 0;
            }
            else if (p == 0)
            {
                // All roots real, at least two are equal.
                float term1 = b * _oneThird;
                float r = -(27f * d) + b * (9f * c - 2f * (b * b));
                float r13 = (r < 0) ? (float)(-Math.Pow(-r, _oneThird)) : (float)Math.Pow(r, _oneThird);
                x1 = -term1 + 2f * r13;
                x2 = -(r13 + term1);
                x3 = x2;
            }
            else
            {
                q = (2f * b * b * b - 9f * a * b * c + 27f * a * a * d) / (27f * a * a * a);
                //
                tmp1 = (3f * q) / (2f * p) * (float)Math.Sqrt(-3f / p);
                if (tmp1 > 1f) tmp1 = 1f;
                else if (tmp1 < -1f) tmp1 = -1f;
                alpha = _oneThird * (float)Math.Acos(tmp1);
                //
                tmp1 = 2f * (float)Math.Sqrt(-p / 3f);
                tmp2 = b / (3f * a);
                x1 = tmp1 * (float)Math.Cos(alpha) - tmp2;
                x2 = tmp1 * (float)Math.Cos(alpha - _twoPiThirds) - tmp2;
                x3 = tmp1 * (float)Math.Cos(alpha - _fourPiThirds) - tmp2;
            }
        }
        public static void GetPrincipalValuesFromMatrix(double s11, double s22, double s33,
                                                        double s12, double s23, double s31,
                                                        ref float x1f, ref float x2f, ref float x3f)
        {
            // https://en.wikipedia.org/wiki/Cubic_function
            // https://www.easycalculation.com/algebra/cubic-equation.php - check source
            double x1 = 0;
            double x2 = 0;
            double x3 = 0;
            //
            double I1 = s11 + s22 + s33;
            double I2 = s11 * s22 + s22 * s33 + s33 * s11 - s12 * s12 - s23 * s23 - s31 * s31;
            double I3 = s11 * s22 * s33 - s11 * s23 * s23 - s22 * s31 * s31 - s33 * s12 * s12 + 2.0 * s12 * s23 * s31;
            //
            SolveQubicEquationDepressedCubic(1, -I1, I2, -I3, ref x1, ref x2, ref x3);
            //
            x1f = (float)x1;
            x2f = (float)x2;
            x3f = (float)x3;
        }
    }
}
