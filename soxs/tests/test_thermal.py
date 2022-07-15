import os
import numpy as np
import shutil
import tempfile
from soxs.response import RedistributionMatrixFile
from soxs.thermal_spectra import ApecGenerator, \
    SpexGenerator, MekalGenerator, CloudyCIEGenerator, \
    IGMGenerator
from soxs.spatial import PointSourceModel
from soxs.simput import SimputCatalog, SimputPhotonList
from soxs.instrument_registry import \
    get_instrument_from_registry
from soxs.instrument import instrument_simulator, \
    simulate_spectrum
from soxs.events import write_spectrum
from numpy.random import RandomState
from numpy.testing import assert_allclose, assert_almost_equal
from soxs.tests.utils import spectrum_answer_testing, \
    file_answer_testing

inst_name = "lynx_lxm"

rmf = RedistributionMatrixFile.from_instrument(inst_name)
agen0 = ApecGenerator(0.01, 10.0, 20000, broadening=True)
agen_var0 = ApecGenerator(0.01, 10.0, 20000, var_elem=["O", "Fe"],
                          broadening=True)
agen_nolines0 = ApecGenerator(0.01, 10.0, 20000, broadening=True,
                              nolines=True)
agen_aspl0 = ApecGenerator(0.01, 10.0, 20000, broadening=True,
                           abund_table="aspl")
agen = ApecGenerator(rmf.elo[0], rmf.ehi[-1], rmf.n_e, broadening=True)
agen_var = ApecGenerator(rmf.elo[0], rmf.ehi[-1], rmf.n_e,
                         var_elem=["O", "Fe"], broadening=True)
agen_nolines = ApecGenerator(rmf.elo[0], rmf.ehi[-1], rmf.n_e,
                             broadening=True, nolines=True)
agen_aspl = ApecGenerator(rmf.elo[0], rmf.ehi[-1], rmf.n_e,
                          broadening=True, abund_table="aspl")
agen_nei = ApecGenerator(rmf.elo[0], rmf.ehi[-1], rmf.n_e,
                         broadening=True, nei=True,
                         var_elem=["O^6","O^3","N^4","Ca^5"])

nH_sim = 0.02
kT_sim = 5.0
abund_sim = 0.4
norm_sim = 1.0e-3
redshift = 0.05
O_sim = 0.4
Fe_sim = 0.4

nei_sim = {"O^6": 0.4, "O^3": 0.5, "N^4": 0.7, "Ca^5": 0.9}

exp_time = 5.0e4
area = 40000.0

spec = agen0.get_spectrum(kT_sim, abund_sim, redshift, norm_sim)
spec.apply_foreground_absorption(nH_sim)

spec_var = agen_var0.get_spectrum(kT_sim, abund_sim, redshift, norm_sim,
                                  elem_abund={"O": O_sim, "Fe": Fe_sim})
spec_var.apply_foreground_absorption(nH_sim)

spec_nolines = agen_nolines0.get_spectrum(kT_sim, abund_sim, redshift, norm_sim)
spec_nolines.apply_foreground_absorption(nH_sim)

spec_aspl = agen_aspl0.get_spectrum(kT_sim, abund_sim, redshift, norm_sim)
spec_aspl.apply_foreground_absorption(nH_sim)

spec_nei = agen_nei.get_nei_spectrum(kT_sim, nei_sim, redshift, norm_sim)
spec_nei.apply_foreground_absorption(nH_sim)


def test_thermal(answer_store, answer_dir):

    prng = RandomState(71)

    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)

    spectrum_answer_testing(spec, "thermal_spec.h5", answer_store, answer_dir)

    pt_src_pos = PointSourceModel(30.0, 45.0)
    pt_src = SimputPhotonList.from_models("thermal_model", spec, pt_src_pos,
                                          exp_time, area, prng=prng)
    sim_cat = SimputCatalog.from_source("thermal_model_simput.fits", pt_src,
                                        overwrite=True)

    instrument_simulator("thermal_model_simput.fits", "thermal_model_evt.fits",
                         exp_time, inst_name, [30.0, 45.0], ptsrc_bkgnd=False,
                         foreground=False, instr_bkgnd=False, prng=prng)

    write_spectrum("thermal_model_evt.fits", "thermal_model_evt.pha",
                   overwrite=True)

    file_answer_testing("EVENTS", "thermal_model_evt.fits", answer_store,
                        answer_dir)
    file_answer_testing("SPECTRUM", "thermal_model_evt.pha", answer_store,
                        answer_dir)

    os.chdir(curdir)
    shutil.rmtree(tmpdir)


def test_thermal_from_spectrum(answer_store, answer_dir):

    prng = RandomState(89)

    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)

    inst = get_instrument_from_registry(inst_name)

    simulate_spectrum(spec, inst["name"], exp_time,
                      "thermal_model_spec_evt.pha", prng=prng)

    file_answer_testing("SPECTRUM", "thermal_model_spec_evt.pha",
                        answer_store, answer_dir)

    os.chdir(curdir)
    shutil.rmtree(tmpdir)


def test_var_thermal():
    assert_allclose(spec.ebins, spec_var.ebins)
    assert_allclose(spec.flux, spec_var.flux)


def test_nolines_thermal_from_spectrum(answer_store, answer_dir):

    prng = RandomState(101)

    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)

    inst = get_instrument_from_registry(inst_name)

    simulate_spectrum(spec_nolines, inst["name"], exp_time,
                      "nolines_thermal_model_evt.pha", prng=prng)

    file_answer_testing("SPECTRUM", "nolines_thermal_model_evt.pha",
                        answer_store, answer_dir)

    os.chdir(curdir)
    shutil.rmtree(tmpdir)


def test_thermal_abund_table(answer_store, answer_dir):

    prng = RandomState(72)

    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)

    spectrum_answer_testing(spec_aspl, "thermal_aspl_spec.h5", answer_store,
                            answer_dir)

    pt_src_pos = PointSourceModel(30.0, 45.0)
    pt_src = SimputPhotonList.from_models("thermal_model_aspl", spec_aspl,
                                          pt_src_pos, exp_time, area, 
                                          prng=prng)
    sim_cat = SimputCatalog.from_source("thermal_model_aspl_simput.fits",
                                        pt_src, overwrite=True)

    instrument_simulator("thermal_model_aspl_simput.fits",
                         "thermal_model_aspl_evt.fits", exp_time, inst_name,
                         [30.0, 45.0], ptsrc_bkgnd=False, foreground=False,
                         instr_bkgnd=False, prng=prng)

    write_spectrum("thermal_model_aspl_evt.fits",
                   "thermal_model_aspl_evt.pha",
                   overwrite=True)

    file_answer_testing("EVENTS", "thermal_model_aspl_evt.fits", answer_store,
                        answer_dir)
    file_answer_testing("SPECTRUM", "thermal_model_aspl_evt.pha", answer_store,
                        answer_dir)

    os.chdir(curdir)
    shutil.rmtree(tmpdir)


def test_thermal_nei(answer_store, answer_dir):

    prng = RandomState(71)

    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)

    spectrum_answer_testing(spec_nei, "thermal_spec_nei.h5", answer_store,
                            answer_dir)

    pt_src_pos = PointSourceModel(30.0, 45.0)
    pt_src = SimputPhotonList.from_models("thermal_model_nei", spec_nei,
                                          pt_src_pos, exp_time, area, prng=prng)
    sim_cat = SimputCatalog.from_source("thermal_model_nei_simput.fits",
                                        pt_src, overwrite=True)

    instrument_simulator("thermal_model_nei_simput.fits",
                         "thermal_model_nei_evt.fits",
                         exp_time, inst_name, [30.0, 45.0], ptsrc_bkgnd=False,
                         foreground=False, instr_bkgnd=False, prng=prng)

    write_spectrum("thermal_model_nei_evt.fits", "thermal_model_nei_evt.pha",
                   overwrite=True)

    file_answer_testing("EVENTS", "thermal_model_nei_evt.fits", answer_store,
                        answer_dir)
    file_answer_testing("SPECTRUM", "thermal_model_nei_evt.pha", answer_store,
                        answer_dir)

    os.chdir(curdir)
    shutil.rmtree(tmpdir)


def test_spex(answer_store, answer_dir):
    spex0 = SpexGenerator(0.01, 10.0, 20000, broadening=True)
    spex_var0 = SpexGenerator(0.01, 10.0, 20000, var_elem=["O", "Fe"],
                              broadening=True)
    specx = spex0.get_spectrum(kT_sim, abund_sim, redshift, norm_sim)
    specx.apply_foreground_absorption(nH_sim)

    specx_var = spex_var0.get_spectrum(kT_sim, abund_sim, redshift, norm_sim,
                                      elem_abund={"O": O_sim, "Fe": Fe_sim})
    specx_var.apply_foreground_absorption(nH_sim)

    assert_allclose(specx.ebins, specx_var.ebins)
    assert_allclose(specx.flux, specx_var.flux)

    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)

    spectrum_answer_testing(specx, "spex_spectrum.h5", answer_store,
                            answer_dir)

    os.chdir(curdir)
    shutil.rmtree(tmpdir)


def test_mekal(answer_store, answer_dir):
    mgen = MekalGenerator(0.01, 10.0, 20000)
    mgen_var = MekalGenerator(0.01, 10.0, 20000, var_elem=["O", "Fe"])
    specm = mgen.get_spectrum(kT_sim, abund_sim, redshift, norm_sim)

    specm_var = mgen_var.get_spectrum(kT_sim, abund_sim, redshift, norm_sim,
                                      elem_abund={"O": O_sim, "Fe": Fe_sim})

    assert_allclose(specm.ebins, specm_var.ebins)
    assert_allclose(specm.flux, specm_var.flux)

    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)

    spectrum_answer_testing(specm, "mekal_spectrum.h5", answer_store,
                            answer_dir)

    os.chdir(curdir)
    shutil.rmtree(tmpdir)


def test_linlog():
    agen0_lin = ApecGenerator(0.01, 10.0, 20000, binscale="linear")
    spec_lin = agen0_lin.get_spectrum(kT_sim, abund_sim, redshift, norm_sim)
    agen0_log = ApecGenerator(0.01, 10.0, 20000, binscale="log")
    spec_log = agen0_log.get_spectrum(kT_sim, abund_sim, redshift, norm_sim)
    assert_almost_equal(spec_lin.total_flux.value, spec_log.total_flux.value)
    assert_almost_equal(spec_lin.total_energy_flux.value, spec_log.total_energy_flux.value)
