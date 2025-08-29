def write_regionProperties_file(file_path, particle_names):

    region_str = "(" + " ".join(particle_names) + ")"

    content = f"""
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      regionProperties;
}}

regions
(
    fluid       ()
    solid       {region_str}
);
    """

    with open(file_path, 'w') as f:
        f.write(content)


