using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;

namespace pymfxshadergen
{
    class Program
    {
        public class ShaderInfo
        {
            public string Name { get; set; }
            public uint Hash { get; set; }
            public List<ShaderInputInfo> Inputs { get; set; }

            public ShaderInfo()
            {
                Inputs = new List<ShaderInputInfo>();
            }
        }

        public class ShaderInputInfo
        {
            public int Offset { get; set; }
            public int Type { get; set; }
            public string Name { get; set; }
            public int ComponentCount { get; set; }
            public ShaderInputInfo AliasOf { get; set; }
        }

        public enum ShaderInputLayoutElementType
        {
            F32 = 1, // 32 bit single precision float
            F16 = 2, // 16 bit half precision float
            IU16 = 3, // guess, 16 bit integer (joint index)
            IS16 = 4, // guess, 16 bit integer (joint index)
            FS16 = 5, // guess, 16 bit normalized compressed float, divisor = 1 << 15 - 1
            IS8 = 7, // guess
            IU8 = 8, // guess, 8 bit unsigned joint index
            FU8 = 9, // guess, 8 bit normalized compressed float, divisor = 255
            FS8 = 10, // guess,  8 bit normalized compressed float, divisor = 127
            _11_11_11_10 = 11, // guess, 4 bytes, used for normals
            RGB = 13, // guess, 1 byte, used for colors without alpha
            RGBA = 14, // guess
        }

        static void Main( string[] args )
        {
            var shaders = new List<ShaderInfo>();
            var shaderHashes = File.ReadAllLines( "shaderhashes.csv" );
            foreach ( var item in shaderHashes.Skip( 1 ) )
            {
                var elems = item.Split( "," );
                var name = elems[ 1 ];
                var hash = elems[ 2 ];
                if ( string.IsNullOrEmpty( hash ) )
                    continue;

                shaders.Add( new ShaderInfo() { Name = name, Hash = uint.Parse( hash, System.Globalization.NumberStyles.HexNumber ) } );
            }

            var shaderInputs = File.ReadAllLines( "shaderinputs.csv" );
            foreach ( var item in shaderInputs.Skip( 1 ) )
            {
                var elems = item.Split( "," );
                //shader,offset,type,name,componentcount
                var shaderName = elems[ 0 ];
                var offset = int.Parse( elems[ 1 ] );
                var type = int.Parse( elems[ 2 ] );
                var name = elems[ 3 ];
                var compcnt = int.Parse( elems[ 4 ] );
                var shader = shaders.Find( x => x.Name == shaderName );

                var input = shader.Inputs.Find( x => x.Name == name );
                if ( input != null )
                {
                    // Multidimensional array
                    var idx = shader.Inputs.Count( x => x.Name.Contains( name ) );

                    input = new ShaderInputInfo() { Offset = offset, Type = type, Name = name, ComponentCount = compcnt };
                }
                else
                {
                    input = new ShaderInputInfo() { Offset = offset, Type = type, Name = name, ComponentCount = compcnt };
                }

                var aliasOf = shader.Inputs.Find( x => x.Offset == input.Offset );
                if ( aliasOf != null )
                    input.AliasOf = aliasOf;

                shader.Inputs.Add( input );
            }

            string FixName( string s )
                => s.Replace( "$", "_DOLLAR_" );

            using var writer = File.CreateText( "mt_shared.generated.bt" );
            writer.WriteLine( @"
#ifndef MT_MOD_GENERATED_BT
#define MT_MOD_GENERATED_BT
#include ""mt_shared.bt""" );

            writer.WriteLine( "typedef enum<uint> {" );
            foreach ( var shader in shaders )
            {
                writer.WriteLine( $" SO_{FixName(shader.Name)} = 0x{shader.Hash:X8}," );
            }
            writer.WriteLine( "} rShaderObjectHash;" );
            writer.WriteLine();

            foreach ( var shader in shaders )
            {
                if ( shader.Inputs.Count == 0 ) continue;

                writer.WriteLine( "typedef struct {" );
                writer.WriteLine( " local int64 p = FTell();" );
                var nameHistory = new HashSet<string>();

                foreach ( var input in shader.Inputs )
                {
                    /*
                     *                 case rShaderInputLayoutElementType_F32: type = "f32"; break;
                case rShaderInputLayoutElementType_F16: type = "f16"; break;
                case rShaderInputLayoutElementType_IU16: type = "u16"; break;
                case rShaderInputLayoutElementType_IS16: type = "s16"; break;
                case rShaderInputLayoutElementType_FS16: type = "fs16"; break;
                case rShaderInputLayoutElementType_IS8: type = "s8"; break;
                case rShaderInputLayoutElementType_IU8: type = "u8"; break;
                case rShaderInputLayoutElementType_FU8: type = "fu8"; break;
                case rShaderInputLayoutElementType_FS8: type = "fs8"; break;
                case rShaderInputLayoutElementType_11_11_11_10: type = "vec432"; break;
                case rShaderInputLayoutElementType_RGB: type = "color8"; break;
                case rShaderInputLayoutElementType_RGBA: type = "color32"; break;
                     */

                    var type = $"type({input.Type})";
                    switch ( (ShaderInputLayoutElementType)input.Type )
                    {
                        case ShaderInputLayoutElementType.F32:
                            type = "f32";
                            break;
                        case ShaderInputLayoutElementType.F16:
                            type = "f16";
                            break;
                        case ShaderInputLayoutElementType.IU16:
                            type = "u16";
                            break;
                        case ShaderInputLayoutElementType.IS16:
                            type = "s16";
                            break;
                        case ShaderInputLayoutElementType.FS16:
                            type = "fs16";
                            break;
                        case ShaderInputLayoutElementType.IS8:
                            type = "s8";
                            break;
                        case ShaderInputLayoutElementType.IU8:
                            type = "u8";
                            break;
                        case ShaderInputLayoutElementType.FU8:
                            type = "fu8";
                            break;
                        case ShaderInputLayoutElementType.FS8:
                            type = "fs8";
                            break;
                        case ShaderInputLayoutElementType._11_11_11_10:
                            type = "vec432";
                            break;
                        case ShaderInputLayoutElementType.RGB:
                            type = "color8";
                            break;
                        case ShaderInputLayoutElementType.RGBA:
                            type = "color32";
                            break;
                        default:
                            break;
                    }

                    var name = input.Name;
                    var nameIdx = 2;
                    while ( !nameHistory.Add( name ) )
                        name = name + "_" + nameIdx++;

                    writer.WriteLine( $" FSeek( p + {input.Offset} ); {type} {name}[{input.ComponentCount}];" );
                }

                writer.WriteLine( $"}} rVertexShaderInputLayout_{FixName(shader.Name)};" );
                writer.WriteLine();
            }
            writer.WriteLine();

            writer.WriteLine( "void ReadVertexBuffer( rShaderHash shader, int vertexCount ) {" );
            writer.WriteLine( " switch ( shader ) {" );
            foreach ( var shader in shaders )
            {
                if ( shader.Inputs.Count == 0 ) continue;
                writer.WriteLine( $"  case SHADER_{FixName(shader.Name)}: rVertexShaderInputLayout_{FixName(shader.Name)} VertexBuffer[ vertexCount ]; break;" );
            }
            writer.WriteLine( " }" );
            writer.WriteLine( "}" );
            writer.WriteLine( "#endif" );
        }

        private static void GeneratePythonCode( List<ShaderInfo> shaders )
        {
            using var writer = File.CreateText( "mfx.py" );
            foreach ( var shader in shaders )
            {
                if ( shader.Inputs.Count == 0 )
                    continue;

                writer.WriteLine( $"class Shader{shader.Name}InputLayout:" );

                // init
                writer.WriteLine( $"    def __init__(self):" );
                foreach ( var input in shader.Inputs )
                {
                    if ( input.AliasOf != null )
                        continue;

                    var defaultValue = 0;
                    writer.WriteLine( $"        self._{input.Name} = {defaultValue}" );
                }
                writer.WriteLine();

                // read
                writer.WriteLine( $"    def read(self, bs):" );
                writer.WriteLine( "        p = bs.tell()" );
                foreach ( var input in shader.Inputs )
                {
                    if ( input.AliasOf != null )
                        continue;

                    var readFn = "bs.readInt()";
                    writer.WriteLine( $"        bs.seek( p + {input.Offset} )" );
                    writer.WriteLine( $"        self._{input.Name} = {readFn}" );
                }
                writer.WriteLine();

                // write
                writer.WriteLine( $"    def write(self, bs):" );
                writer.WriteLine( "        p = bs.tell()" );
                foreach ( var input in shader.Inputs )
                {
                    if ( input.AliasOf != null )
                        continue;

                    var writeFn = "writeInt";
                    writer.WriteLine( $"        bs.seek( p + {input.Offset} )" );
                    writer.WriteLine( $"        bs.{writeFn}(self._{input.Name})" );
                }
                writer.WriteLine();

                // get/set

                foreach ( var input in shader.Inputs )
                {
                    var src = input;
                    if ( src.AliasOf != null )
                        src = src.AliasOf;

                    writer.WriteLine( $"    def get{input.Name}(self):" );
                    writer.WriteLine( $"        return self._{src.Name}" );
                    writer.WriteLine();

                    writer.WriteLine( $"    def set{input.Name}(self, value):" );
                    writer.WriteLine( $"        self._{src.Name} = value" );
                    writer.WriteLine();
                }
                writer.WriteLine();
            }

            writer.WriteLine( "def getShaderInputLayoutByHash( hash ):" );
            foreach ( var shader in shaders )
            {
                if ( shader.Inputs.Count == 0 )
                    continue;

                writer.WriteLine( $"    if hash == 0x{shader.Hash:X8}:" );
                writer.WriteLine( $"        return Shader{shader.Name}InputLayout()" );
            }

            writer.WriteLine( "    return None" );
            writer.WriteLine();

            writer.WriteLine( "def getShaderInputLayoutByName( name ):" );
            foreach ( var shader in shaders )
            {
                if ( shader.Inputs.Count == 0 )
                    continue;

                writer.WriteLine( $"    if name == '{shader.Name}':" );
                writer.WriteLine( $"        return Shader{shader.Name}InputLayout()" );
            }

            writer.WriteLine( "    return None" );
            writer.WriteLine();
        }
    }
}
