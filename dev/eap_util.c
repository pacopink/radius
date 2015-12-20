#include <Python.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "freeradius-devel/build.h"
#include "freeradius-devel/libradius.h"
#include "eap_sim.h"

PyObject *PyFIPS186_2PRF(PyObject* X, PyObject* args)
{
    uint8_t *mk = NULL;
    uint8_t fk[160];
    char *p = NULL;
    int ilen = 0;
    memset(fk, 0, sizeof(fk));
    
    int ok = PyArg_ParseTuple( args, "s#", &p, &ilen);
    if(!ok || ilen!=20) {
        return Py_BuildValue("(OO)", Py_BuildValue("i", 0), Py_BuildValue("s", fk));
    }
    mk = (uint8_t*)p;
    //invoke the algrothm from freeradius
    fips186_2prf(mk, fk); 
    //return Py_BuildValue("(OO)", Py_BuildValue("i", 1), Py_BuildValue("s#i", fk, 160));
    return Py_BuildValue("(OO)", Py_BuildValue("i", 1), Py_BuildValue("s#", fk, sizeof(fk)));
}

static PyMethodDef eap_util_methods[] = {
    {"fips186_2prf", PyFIPS186_2PRF, METH_VARARGS},
    {NULL, NULL}
};

PyMODINIT_FUNC initeap_util(void)
{
    Py_InitModule("eap_util", eap_util_methods);
    //Add const values to module 
    //PyObject* pMod = PyImport_ImportModule("eap_util");
}
