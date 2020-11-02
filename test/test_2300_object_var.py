#------------------------------------------------------------------------------
# Copyright (c) 2016, 2020, Oracle and/or its affiliates. All rights reserved.
#
# Portions Copyright 2007-2015, Anthony Tuininga. All rights reserved.
#
# Portions Copyright 2001-2007, Computronix (Canada) Ltd., Edmonton, Alberta,
# Canada. All rights reserved.
#------------------------------------------------------------------------------

"""
2300 - Module for testing object variables
"""

import TestEnv

import cx_Oracle
import datetime
import decimal

class TestCase(TestEnv.BaseTestCase):

    def __GetObjectAsTuple(self, obj):
        if obj.type.iscollection:
            value = []
            for v in obj.aslist():
                if isinstance(v, cx_Oracle.Object):
                    v = self.__GetObjectAsTuple(v)
                elif isinstance(value, cx_Oracle.LOB):
                    v = v.read()
                value.append(v)
            return value
        attributeValues = []
        for attribute in obj.type.attributes:
            value = getattr(obj, attribute.name)
            if isinstance(value, cx_Oracle.Object):
                value = self.__GetObjectAsTuple(value)
            elif isinstance(value, cx_Oracle.LOB):
                value = value.read()
            attributeValues.append(value)
        return tuple(attributeValues)

    def __TestData(self, expectedIntValue, expectedObjectValue,
            expectedArrayValue):
        intValue, objectValue, arrayValue = self.cursor.fetchone()
        if objectValue is not None:
            objectValue = self.__GetObjectAsTuple(objectValue)
        if arrayValue is not None:
            arrayValue = arrayValue.aslist()
        self.assertEqual(intValue, expectedIntValue)
        self.assertEqual(objectValue, expectedObjectValue)
        self.assertEqual(arrayValue, expectedArrayValue)

    def test_2300_BindNullIn(self):
        "2300 - test binding a null value (IN)"
        var = self.cursor.var(cx_Oracle.DB_TYPE_OBJECT,
                typename = "UDT_OBJECT")
        result = self.cursor.callfunc("pkg_TestBindObject.GetStringRep", str,
                (var,))
        self.assertEqual(result, "null")

    def test_2301_BindObjectIn(self):
        "2301 - test binding an object (IN)"
        typeObj = self.connection.gettype("UDT_OBJECT")
        obj = typeObj.newobject()
        obj.NUMBERVALUE = 13
        obj.STRINGVALUE = "Test String"
        result = self.cursor.callfunc("pkg_TestBindObject.GetStringRep", str,
                (obj,))
        self.assertEqual(result,
                "udt_Object(13, 'Test String', null, null, null, null, null)")
        obj.NUMBERVALUE = None
        obj.STRINGVALUE = "Test With Dates"
        obj.DATEVALUE = datetime.datetime(2016, 2, 10)
        obj.TIMESTAMPVALUE = datetime.datetime(2016, 2, 10, 14, 13, 50)
        result = self.cursor.callfunc("pkg_TestBindObject.GetStringRep", str,
                (obj,))
        self.assertEqual(result,
                "udt_Object(null, 'Test With Dates', null, " \
                "to_date('2016-02-10', 'YYYY-MM-DD'), " \
                "to_timestamp('2016-02-10 14:13:50', " \
                        "'YYYY-MM-DD HH24:MI:SS'), " \
                "null, null)")
        obj.DATEVALUE = None
        obj.TIMESTAMPVALUE = None
        subTypeObj = self.connection.gettype("UDT_SUBOBJECT")
        subObj = subTypeObj.newobject()
        subObj.SUBNUMBERVALUE = decimal.Decimal("18.25")
        subObj.SUBSTRINGVALUE = "Sub String"
        obj.SUBOBJECTVALUE = subObj
        result = self.cursor.callfunc("pkg_TestBindObject.GetStringRep", str,
                (obj,))
        self.assertEqual(result,
                "udt_Object(null, 'Test With Dates', null, null, null, " \
                "udt_SubObject(18.25, 'Sub String'), null)")

    def test_2302_CopyObject(self):
        "2302 - test copying an object"
        typeObj = self.connection.gettype("UDT_OBJECT")
        obj = typeObj()
        obj.NUMBERVALUE = 5124
        obj.STRINGVALUE = "A test string"
        obj.DATEVALUE = datetime.datetime(2016, 2, 24)
        obj.TIMESTAMPVALUE = datetime.datetime(2016, 2, 24, 13, 39, 10)
        copiedObj = obj.copy()
        self.assertEqual(obj.NUMBERVALUE, copiedObj.NUMBERVALUE)
        self.assertEqual(obj.STRINGVALUE, copiedObj.STRINGVALUE)
        self.assertEqual(obj.DATEVALUE, copiedObj.DATEVALUE)
        self.assertEqual(obj.TIMESTAMPVALUE, copiedObj.TIMESTAMPVALUE)

    def test_2303_EmptyCollectionAsList(self):
        "2303 - test getting an empty collection as a list"
        typeName = "UDT_ARRAY"
        typeObj = self.connection.gettype(typeName)
        obj = typeObj.newobject()
        self.assertEqual(obj.aslist(), [])

    def test_2304_FetchData(self):
        "2304 - test fetching objects"
        self.cursor.execute("alter session set time_zone = 'UTC'")
        self.cursor.execute("""
                select
                  IntCol,
                  ObjectCol,
                  ArrayCol
                from TestObjects
                order by IntCol""")
        self.assertEqual(self.cursor.description,
                [ ('INTCOL', cx_Oracle.DB_TYPE_NUMBER, 10, None, 9, 0, 0),
                  ('OBJECTCOL', cx_Oracle.DB_TYPE_OBJECT, None, None, None,
                        None, 1),
                  ('ARRAYCOL', cx_Oracle.DB_TYPE_OBJECT, None, None, None,
                        None, 1) ])
        self.__TestData(1, (1, 'First row', 'First     ', 'N First Row',
                'N First   ', b'Raw Data 1', 2, 5, 12.125, 0.5, 12.5, 25.25,
                50.125, cx_Oracle.Timestamp(2007, 3, 6, 0, 0, 0),
                cx_Oracle.Timestamp(2008, 9, 12, 16, 40),
                cx_Oracle.Timestamp(2009, 10, 13, 17, 50),
                cx_Oracle.Timestamp(2010, 11, 14, 18, 55),
                'Short CLOB value', 'Short NCLOB Value', b'Short BLOB value',
                (11, 'Sub object 1'),
                [(5, 'first element'), (6, 'second element')]),
                [5, 10, None, 20])
        self.__TestData(2, None, [3, None, 9, 12, 15])
        self.__TestData(3, (3, 'Third row', 'Third     ', 'N Third Row',
                'N Third   ', b'Raw Data 3', 4, 10, 6.5, 0.75, 43.25, 86.5,
                192.125, cx_Oracle.Timestamp(2007, 6, 21, 0, 0, 0),
                cx_Oracle.Timestamp(2007, 12, 13, 7, 30, 45),
                cx_Oracle.Timestamp(2017, 6, 21, 23, 18, 45),
                cx_Oracle.Timestamp(2017, 7, 21, 8, 27, 13),
                'Another short CLOB value', 'Another short NCLOB Value',
                b'Yet another short BLOB value',
                (13, 'Sub object 3'),
                [(10, 'element #1'), (20, 'element #2'),
                 (30, 'element #3'), (40, 'element #4')]), None)

    def test_2305_GetObjectType(self):
        "2305 - test getting object type"
        typeObj = self.connection.gettype("UDT_OBJECT")
        self.assertEqual(typeObj.iscollection, False)
        self.assertEqual(typeObj.schema, self.connection.username.upper())
        self.assertEqual(typeObj.name, "UDT_OBJECT")
        subObjectValueType = self.connection.gettype("UDT_SUBOBJECT")
        subObjectArrayType = self.connection.gettype("UDT_OBJECTARRAY")
        expectedAttributeNames = ["NUMBERVALUE", "STRINGVALUE",
                "FIXEDCHARVALUE", "NSTRINGVALUE", "NFIXEDCHARVALUE",
                "RAWVALUE", "INTVALUE", "SMALLINTVALUE", "REALVALUE",
                "DOUBLEPRECISIONVALUE", "FLOATVALUE", "BINARYFLOATVALUE",
                "BINARYDOUBLEVALUE", "DATEVALUE", "TIMESTAMPVALUE",
                "TIMESTAMPTZVALUE", "TIMESTAMPLTZVALUE", "CLOBVALUE",
                "NCLOBVALUE", "BLOBVALUE", "SUBOBJECTVALUE", "SUBOBJECTARRAY"]
        actualAttributeNames = [a.name for a in typeObj.attributes]
        self.assertEqual(actualAttributeNames, expectedAttributeNames)
        expectedAttributeTypes = [cx_Oracle.DB_TYPE_NUMBER,
                cx_Oracle.DB_TYPE_VARCHAR, cx_Oracle.DB_TYPE_CHAR,
                cx_Oracle.DB_TYPE_NVARCHAR, cx_Oracle.DB_TYPE_NCHAR,
                cx_Oracle.DB_TYPE_RAW, cx_Oracle.DB_TYPE_NUMBER,
                cx_Oracle.DB_TYPE_NUMBER, cx_Oracle.DB_TYPE_NUMBER,
                cx_Oracle.DB_TYPE_NUMBER, cx_Oracle.DB_TYPE_NUMBER,
                cx_Oracle.DB_TYPE_BINARY_FLOAT,
                cx_Oracle.DB_TYPE_BINARY_DOUBLE,
                cx_Oracle.DB_TYPE_DATE, cx_Oracle.DB_TYPE_TIMESTAMP,
                cx_Oracle.DB_TYPE_TIMESTAMP_TZ,
                cx_Oracle.DB_TYPE_TIMESTAMP_LTZ, cx_Oracle.DB_TYPE_CLOB,
                cx_Oracle.DB_TYPE_NCLOB, cx_Oracle.DB_TYPE_BLOB,
                subObjectValueType, subObjectArrayType]
        actualAttributeTypes = [a.type for a in typeObj.attributes]
        self.assertEqual(actualAttributeTypes, expectedAttributeTypes)
        self.assertEqual(subObjectArrayType.iscollection, True)
        self.assertEqual(subObjectArrayType.attributes, [])

    def test_2306_ObjectType(self):
        "2306 - test object type data"
        self.cursor.execute("""
                select ObjectCol
                from TestObjects
                where ObjectCol is not null
                  and rownum <= 1""")
        objValue, = self.cursor.fetchone()
        self.assertEqual(objValue.type.schema,
                self.connection.username.upper())
        self.assertEqual(objValue.type.name, "UDT_OBJECT")
        self.assertEqual(objValue.type.attributes[0].name, "NUMBERVALUE")

    def test_2307_RoundTripObject(self):
        "2307 - test inserting and then querying object with all data types"
        self.cursor.execute("alter session set time_zone = 'UTC'")
        self.cursor.execute("truncate table TestClobs")
        self.cursor.execute("truncate table TestNClobs")
        self.cursor.execute("truncate table TestBlobs")
        self.cursor.execute("insert into TestClobs values " \
                "(1, 'A short CLOB')")
        self.cursor.execute("insert into TestNClobs values " \
                "(1, 'A short NCLOB')")
        self.cursor.execute("insert into TestBlobs values " \
                "(1, utl_raw.cast_to_raw('A short BLOB'))")
        self.connection.commit()
        self.cursor.execute("select CLOBCol from TestClobs")
        clob, = self.cursor.fetchone()
        self.cursor.execute("select NCLOBCol from TestNClobs")
        nclob, = self.cursor.fetchone()
        self.cursor.execute("select BLOBCol from TestBlobs")
        blob, = self.cursor.fetchone()
        typeObj = self.connection.gettype("UDT_OBJECT")
        obj = typeObj.newobject()
        obj.NUMBERVALUE = 5
        obj.STRINGVALUE = "A string"
        obj.FIXEDCHARVALUE = "Fixed str"
        obj.NSTRINGVALUE = "A NCHAR string"
        obj.NFIXEDCHARVALUE = "Fixed N"
        obj.RAWVALUE = b"Raw Value"
        obj.INTVALUE = 27
        obj.SMALLINTVALUE = 13
        obj.REALVALUE = 184.875
        obj.DOUBLEPRECISIONVALUE = 1.375
        obj.FLOATVALUE = 23.75
        obj.DATEVALUE = datetime.date(2017, 5, 9)
        obj.TIMESTAMPVALUE = datetime.datetime(2017, 5, 9, 9, 41, 13)
        obj.TIMESTAMPTZVALUE = datetime.datetime(1986, 8, 2, 15, 27, 38)
        obj.TIMESTAMPLTZVALUE = datetime.datetime(1999, 11, 12, 23, 5, 2)
        obj.BINARYFLOATVALUE = 14.25
        obj.BINARYDOUBLEVALUE = 29.1625
        obj.CLOBVALUE = clob
        obj.NCLOBVALUE = nclob
        obj.BLOBVALUE = blob
        subTypeObj = self.connection.gettype("UDT_SUBOBJECT")
        subObj = subTypeObj.newobject()
        subObj.SUBNUMBERVALUE = 23
        subObj.SUBSTRINGVALUE = "Substring value"
        obj.SUBOBJECTVALUE = subObj
        self.cursor.execute("insert into TestObjects (IntCol, ObjectCol) " \
                "values (4, :obj)", obj = obj)
        self.cursor.execute("""
                select IntCol, ObjectCol, ArrayCol
                from TestObjects
                where IntCol = 4""")
        self.__TestData(4, (5, 'A string', 'Fixed str ', 'A NCHAR string',
                'Fixed N   ', b'Raw Value', 27, 13, 184.875, 1.375, 23.75,
                14.25, 29.1625, cx_Oracle.Timestamp(2017, 5, 9, 0, 0, 0),
                cx_Oracle.Timestamp(2017, 5, 9, 9, 41, 13),
                cx_Oracle.Timestamp(1986, 8, 2, 15, 27, 38),
                cx_Oracle.Timestamp(1999, 11, 12, 23, 5, 2),
                'A short CLOB', 'A short NCLOB', b'A short BLOB',
                (23, 'Substring value'), None), None)
        obj.CLOBVALUE = "A short CLOB (modified)"
        obj.NCLOBVALUE = "A short NCLOB (modified)"
        obj.BLOBVALUE = "A short BLOB (modified)"
        self.cursor.execute("insert into TestObjects (IntCol, ObjectCol) " \
                "values (5, :obj)", obj = obj)
        self.cursor.execute("""
                select IntCol, ObjectCol, ArrayCol
                from TestObjects
                where IntCol = 5""")
        self.__TestData(5, (5, 'A string', 'Fixed str ', 'A NCHAR string',
                'Fixed N   ', b'Raw Value', 27, 13, 184.875, 1.375, 23.75,
                14.25, 29.1625, cx_Oracle.Timestamp(2017, 5, 9, 0, 0, 0),
                cx_Oracle.Timestamp(2017, 5, 9, 9, 41, 13),
                cx_Oracle.Timestamp(1986, 8, 2, 15, 27, 38),
                cx_Oracle.Timestamp(1999, 11, 12, 23, 5, 2),
                'A short CLOB (modified)', 'A short NCLOB (modified)',
                b'A short BLOB (modified)',
                (23, 'Substring value'), None), None)
        self.connection.rollback()

    def test_2308_InvalidTypeObject(self):
        "2308 - test trying to find an object type that does not exist"
        self.assertRaises(cx_Oracle.DatabaseError, self.connection.gettype,
                "A TYPE THAT DOES NOT EXIST")

    def test_2309_AppendingWrongObjectType(self):
        "2309 - test appending an object of the wrong type to a collection"
        collectionObjType = self.connection.gettype("UDT_OBJECTARRAY")
        collectionObj = collectionObjType.newobject()
        arrayObjType = self.connection.gettype("UDT_ARRAY")
        arrayObj = arrayObjType.newobject()
        self.assertRaises(cx_Oracle.DatabaseError, collectionObj.append,
                arrayObj)

    def test_2310_ReferencingSubObj(self):
        "2310 - test that referencing a sub object affects the parent object"
        objType = self.connection.gettype("UDT_OBJECT")
        subObjType = self.connection.gettype("UDT_SUBOBJECT")
        obj = objType.newobject()
        obj.SUBOBJECTVALUE = subObjType.newobject()
        obj.SUBOBJECTVALUE.SUBNUMBERVALUE = 5
        obj.SUBOBJECTVALUE.SUBSTRINGVALUE = "Substring"
        self.assertEqual(obj.SUBOBJECTVALUE.SUBNUMBERVALUE, 5)
        self.assertEqual(obj.SUBOBJECTVALUE.SUBSTRINGVALUE, "Substring")

    def test_2311_AccessSubObjectParentObjectDestroyed(self):
        "2311 - test accessing sub object after parent object destroyed"
        objType = self.connection.gettype("UDT_OBJECT")
        subObjType = self.connection.gettype("UDT_SUBOBJECT")
        arrayType = self.connection.gettype("UDT_OBJECTARRAY")
        subObj1 = subObjType.newobject()
        subObj1.SUBNUMBERVALUE = 2
        subObj1.SUBSTRINGVALUE = "AB"
        subObj2 = subObjType.newobject()
        subObj2.SUBNUMBERVALUE = 3
        subObj2.SUBSTRINGVALUE = "CDE"
        obj = objType.newobject()
        obj.SUBOBJECTARRAY = arrayType.newobject([subObj1, subObj2])
        subObjArray = obj.SUBOBJECTARRAY
        del obj
        self.assertEqual(self.__GetObjectAsTuple(subObjArray),
                [(2, "AB"), (3, "CDE")])

    def test_2312_SettingAttrWrongObjectType(self):
        "2312 - test assigning an object of wrong type to an object attribute"
        objType = self.connection.gettype("UDT_OBJECT")
        obj = objType.newobject()
        wrongObjType = self.connection.gettype("UDT_OBJECTARRAY")
        wrongObj = wrongObjType.newobject()
        self.assertRaises(cx_Oracle.DatabaseError, setattr, obj,
                "SUBOBJECTVALUE", wrongObj)

    def test_2313_SettingVarWrongObjectType(self):
        "2313 - test setting value of object variable to wrong object type"
        wrongObjType = self.connection.gettype("UDT_OBJECTARRAY")
        wrongObj = wrongObjType.newobject()
        var = self.cursor.var(cx_Oracle.DB_TYPE_OBJECT,
                typename = "UDT_OBJECT")
        self.assertRaises(cx_Oracle.DatabaseError, var.setvalue, 0, wrongObj)

    def test_2314_StringFormat(self):
        "2314 - test object string format"
        objType = self.connection.gettype("UDT_OBJECT")
        user = TestEnv.GetMainUser()
        self.assertEqual(str(objType),
                "<cx_Oracle.ObjectType %s.UDT_OBJECT>" % user.upper())
        self.assertEqual(str(objType.attributes[0]),
                "<cx_Oracle.ObjectAttribute NUMBERVALUE>")

    def test_2315_TrimCollectionList(self):
        "2315 - test Trim number of elements from collection"
        subObjType = self.connection.gettype("UDT_SUBOBJECT")
        arrayType = self.connection.gettype("UDT_OBJECTARRAY")
        data = [(1, "AB"), (2, "CDE"), (3, "FGH"), (4, "IJK")]
        arrayObj = arrayType()
        for numVal, strVal in data:
            subObj = subObjType()
            subObj.SUBNUMBERVALUE = numVal
            subObj.SUBSTRINGVALUE = strVal
            arrayObj.append(subObj)
        self.assertEqual(self.__GetObjectAsTuple(arrayObj), data)
        arrayObj.trim(2)
        self.assertEqual(self.__GetObjectAsTuple(arrayObj), data[:2])
        arrayObj.trim(1)
        self.assertEqual(self.__GetObjectAsTuple(arrayObj), data[:1])
        arrayObj.trim(0)
        self.assertEqual(self.__GetObjectAsTuple(arrayObj), data[:1])
        arrayObj.trim(1)
        self.assertEqual(self.__GetObjectAsTuple(arrayObj), [])

if __name__ == "__main__":
    TestEnv.RunTestCases()