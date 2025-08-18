import logging
import knime.extension as knext
from knime.types.chemistry import to_rdkit_series, is_molecule
from rdkit import Chem

LOGGER = logging.getLogger(__name__)   
    
@knext.node(name="RDKitMol from any Mol Type", node_type=knext.NodeType.MANIPULATOR, icon_path="icon.png", category="/")
@knext.input_table(name="Input Data", description="Input table containing any mol type")
@knext.output_table(name="Output Data", description="Input table appended with a column containing RDKit molecule")
class RDKitObject:
    """
    This node returns the RDKit molecule in an appended column.
    """
    # Note: is_molecule is used to filter columns that contain any usable molecule type.
    molecule_column = knext.ColumnParameter(label="Select the column containing any mol type", description="Choose the column from the input table containing the mol type", column_filter=is_molecule)

    def configure(self, configure_context, input_schema_1):
        return input_schema_1.append(knext.Column(knext.logical(Chem.Mol), "RDKitMol")) # RDKitMol is a type that is known to KNIME and can be used in the output table.
 
 
    def execute(self, exec_context, input_1):    
        input_1_pandas = input_1.to_pandas()
        #input_1_pandas['RDKitMol'] = input_1_pandas[self.molecule_column].astype("Molecule")  # This is unfortunately not yet supported in KNIME python extensions (2025-07-23)
        input_1_pandas['RDKitMol'] = to_rdkit_series(input_1_pandas[self.molecule_column]) # Note: We can convert any molecule type to RDKitMol using this function. And simply add the new column to the DataFrame.
        return knext.Table.from_pandas(input_1_pandas)
    

@knext.node(name="Count Num Carbons", node_type=knext.NodeType.MANIPULATOR, icon_path="icon.png", category="/")
@knext.input_table(name="Input Data", description="Input table containing RDKit molecules")
@knext.output_table(name="Output Data", description="Input table with a column containing the number of carbons")
class CountNumCarbons:
    """
    This node counts the number of carbons in each RDKit molecule and appends it as a new column.

    The provided KNIME workflow demonstrates how to use this node:
        - directly from a SMILES column
        - from a column containing Java RDKit molecules
        - from another python node that outputs RDKit molecules
    """
    molecule_column = knext.ColumnParameter(label="Select the column containing RDKit molecules", description="Choose the column from the input table containing RDKit molecules", column_filter=is_molecule)
    
    def configure(self, configure_context, input_schema_1):
        LOGGER.warning(f"DEBUG: Input schema : {dir(input_schema_1)}")
        for col in input_schema_1._columns:
            LOGGER.warning(f"Column: {col.name}, Type: {col.ktype}")   # Debugging line to check input types
        return input_schema_1.append(knext.Column(knext.int64(), "NumCarbons"))


    def execute(self, exec_context, input_1):
        df = input_1.to_pandas()
        mol_col = to_rdkit_series(df[self.molecule_column], sanitize=True)
        df['NumCarbons'] = mol_col.apply(lambda mol: sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() == 6))
        return knext.Table.from_pandas(df)
